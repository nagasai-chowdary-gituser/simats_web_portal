
from langgraph.graph import StateGraph, END

from src.state.rag_state import RAGState
from src.nodes.nodes import RAGNodes as SimpleRAGNodes
from src.nodes.reactnode import RAGNodes as AgenticRAGNodes


class GraphBuilder:

    def __init__(self, retriever, llm, use_agentic: bool = False):
        self.use_agentic = use_agentic
        node_cls = AgenticRAGNodes if use_agentic else SimpleRAGNodes
        self.nodes = node_cls(retriever, llm)
        self.graph = None

    def build(self):
        g = StateGraph(RAGState)

        if self.use_agentic:
            g.add_node("agent_responder", self.nodes.generate_answer)
            g.set_entry_point("agent_responder")
            g.add_edge("agent_responder", END)
        else:
            g.add_node("retriever", self.nodes.retrieve_docs)
            g.add_node("responder", self.nodes.generate_answer)

            g.set_entry_point("retriever")
            g.add_edge("retriever", "responder")
            g.add_edge("responder", END)

        self.graph = g.compile()
        return self.graph
