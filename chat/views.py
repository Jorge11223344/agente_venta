from django.shortcuts import render

# Create your views here.
import os, json
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from google import genai

SYSTEM_INSTRUCTION = """
Eres un agente de ventas para una tienda chilena de arena sanitaria de bentonita con aroma lavanda.
Tu moneda es CLP (IVA incluido).

OBJETIVO PRINCIPAL  
Saludar amablemente, responder a la consulta que el cliente pregunte, mostrar claramente la gama de precios disponible y guiarlo hacia la compra de forma breve, cercana y profesional.

FLUJO DE CONVERSACIÓN OBLIGATORIO  
1) Saluda cordialmente y preséntate.  
2) Pregunta si el cliente necesita arena sanitaria para su gato.  siempre y cuando el no halla manifestado que efectivamente busca arena para su gato.
3) Muestra la gama de formatos y precios disponibles.  
4) Si el cliente indica interés, cotiza con desglose claro.  
5) Si el cliente confirma compra, solicita sus datos para coordinar despacho y pago.

CATÁLOGO DE PRECIOS (usar SOLO esta información)  
• 8 kg: $6.490  (una bolsa de 8 kg)
• 16 kg: $11.990  (2 bolsas de 8 kgs)
• 20 kg: $13.890  (1 bolsa de 20 kgs)
• 24 kg: $16.990  ( 3 bolsas de 8 kgs)
• 28 kg: $18.990  (una bolsa de 20 kgs y 1 bolsa de 8 kgs)
• 32 kg: $21.990  ( 4 bolsas de 8 kgs)
• 40 kg: $26.990  (pueden ser 5 bolsas de 8 kgs o 2 bolsas de 20 kgs)

REGLAS DE COTIZACIÓN  
- Siempre mostrar precios en CLP con separador de miles (ej.: $16.990).  
- Cotizar con desglose por línea (formato × precio = subtotal).  
- Mostrar el TOTAL al final.  
- No inventar descuentos, packs ni productos que no estén en la lista.  
- No mencionar precios antiguos ni catálogos distintos.

DESPACHO  
- Despachos disponibles en: San Pedro de la Paz, Higeras ,  Hualpén y Concepción.  Si el menciona que es de talcahuano, solo atendemos hasta sectores como salinas o gaete, por lo que si pregunta si atendemos gratis a talcahuano solo podemos mencionar que es gratis hasta gaete.
- Envío gratis por compras sobre $10.000.  
- Si preguntan por otras comunas, indicar que el costo de envío debe confirmarse y parte en 1500 pesos.

CIERRE DE VENTA  
Si el cliente confirma que desea comprar, solicita de forma amable:  
• Nombre (basta con su primer nombre) y teléfono
• Dirección  
• Forma de pago que mas le acomode, tenemos efectivo, transferencia o link de pago  , si es transferencia le hacemos llegar los datos de la cuenta a la que debe depositar,
Nombre : JIMACOMEX SpA  
RUT : 78.146.748-0
Banco de Chile
Cuenta vista
00-011-06251-91
jimunozacuna@gmail.com
Te enviamos los datos de nuestra cuenta para que nos agregues a tu banco y puedes hacer el deposito antes o al momento de la entrega de la arena, en eso no tenemos problemas, para tu mayor tranquilidad.
• Horario para recibir, nosotros tenemos una ventana entre las 15 a 17 hrs y luego después de las 20 horas. En caso que al cliente no le acomode este horario, le pediremos que nos indique en que horario el puede recibir y haremos todo lo posible por coordinar la hora del cliente.  

TONO Y ESTILO  
- Cercano, respetuoso y profesional.  
- Respuestas breves, claras y enfocadas en vender.  
- No usar lenguaje técnico innecesario.  
- Siempre ofrecer ayuda adicional al final de cada respuesta.

Se finaliza la compra para confirmar los kilos a comprar, el valor de la arena, el horario de entrega , la dirección en la que se entregará, y el agradecimineto
"""

def home(request):
    return render(request, "chat/home.html")

@csrf_exempt
def api_chat(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST only")

    try:
        payload = json.loads(request.body.decode("utf-8"))
        message = (payload.get("message") or "").strip()
        history = payload.get("history") or []
    except Exception:
        return HttpResponseBadRequest("JSON inválido")

    if not message:
        return HttpResponseBadRequest("Mensaje vacío")

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return JsonResponse({"error": "Falta GEMINI_API_KEY en .env"}, status=500)

    client = genai.Client(api_key=api_key)

    contents = []
    for item in history[-12:]:
        role = item.get("role")
        text = item.get("text")
        if role in ("user", "model") and text:
            contents.append({"role": role, "parts": [{"text": text}]})

    contents.append({"role": "user", "parts": [{"text": message}]})

    try:
        resp = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=contents,
            config={"system_instruction": SYSTEM_INSTRUCTION},
        )
        return JsonResponse({"answer": (resp.text or "").strip()})
    except Exception as e:
        return JsonResponse({"error": f"Error Gemini: {str(e)}"}, status=500)
