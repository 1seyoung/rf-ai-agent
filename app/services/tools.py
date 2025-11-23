from typing import List
from langchain.tools import BaseTool
from app.services.tools.decide_tool import decide_furniture
from app.services.tools.place_tool import place_furniture
from app.services.tools.search_tool import search_products

def get_tools() -> List[BaseTool]:
    """모든 Agent Tools 반환"""
    
    tools = [
        decide_furniture,
        place_furniture,
        search_products
    ]
    
    return tools