import sys
sys.path.append(r"E:\vscode_stuff\twr_first\advertisement-info")
import asyncio
import functions_framework
from src.application.usecase import OzonAdvInfoUseCase
import logging

logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",  
)

logger = logging.getLogger(__name__)  

@functions_framework.http
def run_adv_info(request):
    try:
        asyncio.run(OzonAdvInfoUseCase.get_adv_info_ozon())
        return {"status": "success"}, 200
    except Exception as e:
        logger.exception(f"Error executing run_adv_info: {e}")
        return {"status": "error"}, 500

