import asyncio
import functions_framework
from src.application.usecase import OzonAdvInfoUseCase
import logging



logger = logging.getLogger(__name__)  

@functions_framework.http
def run_adv_info(request):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    try:
        use_case = OzonAdvInfoUseCase()
        asyncio.run(use_case())
        return {"status": "success"}, 200
    except Exception as e:
        logger.exception(f"Error executing run_adv_info: {e}")
        return {"status": "error"}, 500

