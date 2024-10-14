def config_graph():
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from langchain_core.messages import ToolMessage
    from langchain_mistralai import ChatMistralAI
    from typing import Annotated, TypedDict
    from langgraph.graph import StateGraph, START, END
    from langgraph.graph.message import add_messages
    from dotenv import load_dotenv
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.prompts import MessagesPlaceholder
    import sys
    from langchain_core.prompts import ChatPromptTemplate
    from typing_extensions import TypedDict
    from langchain_core.messages import ToolMessage
    from langchain_core.runnables import RunnableLambda
    from langgraph.checkpoint.memory import MemorySaver
    from tools.find_protocols import find_protocols
    from tools.analyze_packet import analyze_packet
    from tools.find_router import find_router
    from tools.ip_mac import ip_mac
    from tools.subnet import subnet
    from tools.tcp_session import tcp_session

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    keys_path = os.path.join(BASE_DIR, 'keys.env')
    load_dotenv(dotenv_path=keys_path)

    #environment variables
    mistral_key = os.getenv('MISTRAL_API_KEY')
    llm = ChatMistralAI(model="mistral-large-latest", temperature=0)
    
    primary_assistant_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a helpful customer support assistant for analyzing packet traces. "
                " Use the provided tools to search for protocols, security threats, and other information to assist the user's queries. "
                " When searching, be persistent. Expand your query bounds if the first search returns no results. "
                " If a search comes up empty, expand your search before giving up."
                " Use {PCAP} as the file to analyze."
                " Use {external_context} as extra context."
            ),
            MessagesPlaceholder("messages"),
        ]
    )


    tools = [find_protocols, analyze_packet, find_router, ip_mac, subnet, tcp_session]

    llm_with_tools = llm.bind_tools(tools)

    packto_runnable = primary_assistant_prompt | llm_with_tools

    """
    Define graph state
    This makes it so that every message will be in a list
    and all of those messages will be received to every node
    in the graph when it is called. Nodes are basically just 
    functions. So those functions will be called and they will 
    receive messages state as input
    """
    class AgentState(TypedDict):
        messages: Annotated[list, add_messages]#Annotated[Sequence[BaseMessage], operator.add]
        PCAP: str
        external_context: dict

    #Node to see if we need to keep calling tools to answer the question
    def should_continue(state):
        return "continue" if state["messages"][-1].tool_calls else "end"

    #call the model using the previous messages
    def call_model(state, config):
        response = packto_runnable.invoke(state)
        return {"messages": [response]}

    #execute the tool
    def _invoke_tool(tool_call):
        tool = {tool.name: tool for tool in tools}[tool_call["name"]]
        return ToolMessage(tool.invoke(tool_call["args"]), tool_call_id=tool_call["id"])

    tool_executor = RunnableLambda(_invoke_tool)

    #Decide which tool is best
    def call_tools(state):
        last_message = state["messages"][-1]
        return {"messages": tool_executor.batch(last_message.tool_calls)}

    memory = MemorySaver()

    workflow = StateGraph(AgentState)
    workflow.add_node("agent", call_model)
    workflow.add_node("action", call_tools)
    workflow.set_entry_point("agent")

    """
    Conditional edge so that every time the agent is finished,
    we check if it should continue. If we should, call more tools.
    If not, end.
    """
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "continue": "action",
            "end": END,
        },
    )
    #Allow a connection between action and agent so that the model can call tools
    workflow.add_edge("action", "agent")

    graph = workflow.compile(checkpointer=memory)

    return graph