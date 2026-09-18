import time
from typing import Callable
from fastapi import Request, Response, APIRouter, BackgroundTasks, HTTPException
from fastapi.routing import APIRoute

from app.schemas.schemas import ChatRequest, ChatResponse
from app.services.chat_service import log_to_db_background, generate_response

class LoggingRoute(APIRoute):
    """
    Her chat isteğini ve yanıtını FastAPI'nin yaşam döngüsüne müdahale ederek 
    otomatik ve asenkron bir şekilde DB'ye loglayan özel route sınıfı.
    """

    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            start_time = time.time()

            # Gelen isteğin gövdesini (body) yakalıyoruz
            body = await request.body()
            request_body_str = body.decode("utf-8") if body else ""

            # Asıl endpoint fonksiyonunu çalıştırıp yanıtı alıyoruz
            response: Response = await original_route_handler(request)

            # İşlem süresini hesaplıyoruz
            duration = time.time() - start_time

            # Üretilen yanıtın gövdesini alıyoruz
            response_body_str = ""
            if hasattr(response, "body"):
                response_body_str = response.body.decode("utf-8")

            # Arka plan görevleri (BackgroundTasks) yöneticisini ayarlıyoruz
            if response.background is None:
                bg_tasks = BackgroundTasks()
                response.background = bg_tasks
            else:
                bg_tasks = response.background

            # İstek bittikten hemen sonra arka planda veritabanı loglamasını tetikliyoruz
            bg_tasks.add_task(
                log_to_db_background,
                request_data=request_body_str,
                response_data=response_body_str,
                response_time=duration,

            )

            return response

        return custom_route_handler


# Router tanımlamasında özel LoggingRoute sınıfımızı aktif ediyoruz
router = APIRouter(route_class=LoggingRoute, tags=["Chat & QA"])


@router.post("/chat", response_model=ChatResponse, summary="BDDK Regülasyon Asistanı RAG Yanıtı")
async def chat(request: ChatRequest):
    """
    Kullanıcının sorularını kabul eden ve Milvus ile OpenAI kullanarak
    anlamsal RAG yanıtı dönen ana sohbet endpoint'i.
    """
    try:
        # Chat servisi üzerinden RAG yanıtını üretiyoruz
        result = generate_response(request.message, request.session_id)

        if result is None:
            raise HTTPException(
                status_code=400,
                detail="Rehber koleksiyonu henüz oluşturulmamış. Lütfen önce bir döküman yükleyin."
            )

        return ChatResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Sohbet işlenirken bir hata oluştu: {str(e)}"
        )