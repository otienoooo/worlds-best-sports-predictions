exports.handler = async (event) => {
    if (event.httpMethod !== 'POST') return { statusCode: 200, body: 'ok' };

    const update = JSON.parse(event.body || '{}');
    const msg = update.message;
    if (!msg || !msg.text) return { statusCode: 200, body: 'ok' };

    const chatId = msg.chat.id;
    const text = msg.text.trim();

    async function send(t) {
        await fetch(`https://api.telegram.org/bot${process.env.BOT_TOKEN}/sendMessage`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ chat_id: chatId, text: t, parse_mode: 'HTML' })
        });
    }

    const VIP_LINK = 'https://selar.com/9m75rf1u40';
    const JACKPOT_LINK = 'https://selar.com/87s04q9q81';

    if (text === '/start') {
        await send("⚽ <b>WORLD BEST SPORTS PREDICTIONS</b>\n\n💰 Get VIP access:\n/vip → Standard VIP (KES 500)\n/jackpot → Jackpot VIP (KES 1,000)\n\nPay via M-Pesa & get instant access!");
    } else if (text === '/vip') {
        await send(`👑 <b>STANDARD VIP — KES 500</b>\nPay via M-Pesa here:\n${VIP_LINK}\n\n✅ Your VIP access link is delivered instantly after payment.`);
    } else if (text === '/jackpot') {
        await send(`🏆 <b>JACKPOT VIP — KES 1,000</b>\nPay via M-Pesa here:\n${JACKPOT_LINK}\n\n✅ Your Jackpot access link is delivered instantly after payment.`);
    } else {
        await send("Type /start to see VIP packages.");
    }
    return { statusCode: 200, body: 'ok' };
};
