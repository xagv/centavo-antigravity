import asyncio
import os
from google.antigravity import Agent, LocalAgentConfig

INSTRUCCIONES = """
Eres un validador de contratos de API entre microservicios.
Tu trabajo es comparar los esquemas de request/response expuestos
por dos servicios que se comunican entre sí, y reportar cualquier
incompatibilidad: campos faltantes, tipos de dato distintos, o
cambios que romperían al consumidor.
"""
async def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "\n❌ Falta la variable de entorno GEMINI_API_KEY.\n"
            " 1. Obtén tu key gratuita en: https://aistudio.google.com/app/apikey\n"
            " 2. Expórtala antes de ejecutar el script:\n"
            " export GEMINI_API_KEY='tu-api-key-aqui'\n"
)
    config = LocalAgentConfig(
        system_instructions=INSTRUCCIONES,
        api_key=api_key,
)
    async with Agent(config) as agent:
        response = await agent.chat(
            "Compara el endpoint de transacciones de transactions-service "
            "con lo que espera consumir budgets-service para calcular "
            "sobregasto. ¿Son compatibles? Si no, dime exactamente qué falla."
    )
        print(await response.text())

if __name__ == "__main__":
    asyncio.run(main())