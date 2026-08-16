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

    if (text === '/start') {
        await send("⚽ <b>WORLD BEST SPORTS PREDICTIONS</b>\n\n💰 Pay via M-Pesa right here:\n/vip 0712345678 → Standard VIP (KES 500)\n/jackpot 0712345678 → Jackpot VIP (KES 1,000)\n\n(Replace with your real M-Pesa number)");
        return { statusCode: 200, body: 'ok' };
    }

    const order = text.match(/^\/(vip|jackpot)\s+((?:\+?254|0)(?:7|1)\d{8})$/i);
    if (order) {
        const pkg = order[1].toLowerCase();
        const phone = order[2];
        const amount = pkg === 'vip' ? 500 : 1000;
        const reference = `TG${chatId}-${pkg}`;

        const r = await fetch('https://payment.intasend.com/api/v1/payment/mpesa/stk-push/v1', {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${process.env.INTASEND_PRIVATE_KEY}`, 'Content-Type': 'application/json' },
            body: JSON.stringify({ amount: amount, phone_number: phone, reference: reference, comment: reference })
        });

        if (r.status === 200) {
            await send(`📲 <b>M-Pesa prompt sent to ${phone}!</b>\nEnter your PIN for KES ${amount}.\nYour VIP access link will arrive here automatically after payment. ✅`);
        } else {
            await send("❌ Payment system busy. Please try again in a minute.");
        }
        return { statusCode: 200, body: 'ok' };
    }

    await send("Type /start to see payment instructions.");
    return { statusCode: 200, body: 'ok' };
};
