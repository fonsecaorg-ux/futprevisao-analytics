import logging
from telegram import Update, constants
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# Importações do seu ecossistema Pro
from core.data_loader import load_all_data
from core.assistant import answer as ai_assistant
from core.config import LEAGUE_FILES

# Configurações do Bot
TOKEN = "8481366979:AAF3lSzW_L-3d9keeLIDoZM23blaZ2g0etY"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Boas-vindas e instruções"""
    welcome_text = (
        "⚽ *FutPrevisão Pro V2.0 - Oráculo IA*\n\n"
        "Olá! Estou conectado às *10 ligas* e pronto para analisar.\n\n"
        "📌 *Como usar:*\n"
        "Basta digitar o nome dos times, por exemplo:\n"
        "`Arsenal x Chelsea` ou `Real Madrid vs Betis`\n\n"
        "🛡️ *Diferenciais:* Análise de Linhas Individuais, P80 de Segurança e Blacklist Científica ativada."
    )
    await update.message.reply_text(welcome_text, parse_mode=constants.ParseMode.MARKDOWN)

async def handle_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa a mensagem do usuário e consulta o Oráculo"""
    user_query = update.message.text
    
    # Carrega os dados mais recentes dos seus CSVs
    all_matches, all_referees, _ = load_all_data()
    
    # Chama o Oráculo Inteligente (Melhoria 7 e 30)
    response = ai_assistant(user_query, all_matches, all_referees)
    
    # Formatação para o Telegram
    # Usamos bloco de código para manter o alinhamento do relatório técnico
    formatted_resp = f"📊 *Relatório FutPrevisão Pro*\n\n```\n{response.body}\n```"
    
    await update.message.reply_text(formatted_resp, parse_mode=constants.ParseMode.MARKDOWN)

if __name__ == '__main__':
    # Inicializa o Bot
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_analysis))
    
    print("🚀 analytics_Diego_Bot online e monitorando 10 ligas...")
    application.run_polling()