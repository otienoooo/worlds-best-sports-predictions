exports.handler = async (event) => {
    if (event.httpMethod !== 'POST') return { statusCode: 200, body: 'ok' };
    const body = JSON.parse(event.body || '{}');

    const ref = String(body.reference || body.comment || body.invoice_id || '');
    const status = String(body.status || body.state || '').toLowerCase();

    if (ref.startsWith('TG') && ['success', 'complete', 'completed', 'approved'].includes(status)) {
        const parts = ref.split('-');
        const chatId = parts[0].replace('TG', '');
        const pkg = parts[1] || 'vip';

        // 👇 REPLACE THESE WITH YOUR REAL TELEGRAM INVITE LINKS
        const link = pkg === 'jackpot'
            ? 'https://t.me/+CX-neu-jdUFhNzU0'
            : 'https://t.me/+kus3LRV4qAw4ZjFk';

        await fetch(`https://api.telegram.org/bot${process.env.BOT_TOKEN}/sendMessage`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                chat_id: chatId,
                text: `🎉 <b>Payment received!</b>\nWelcome to ${pkg === 'jackpot' ? '🏆 JACKPOT VIP' : '👑 STANDARD VIP'}. Join now:\n${link}`,
                parse_mode: 'HTML'
            })
        });
    }
    return { statusCode: 200, body: 'ok' };
};
