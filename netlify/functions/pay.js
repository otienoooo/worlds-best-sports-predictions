exports.handler = async (event) => {
    if (event.httpMethod !== 'POST') return { statusCode: 405, body: 'Method Not Allowed' };

    const { phone, amount, package_type } = JSON.parse(event.body);
    const secretKey = process.env.INTASEND_PRIVATE_KEY;

    try {
        const response = await fetch('https://payment.intasend.com/api/v1/payment/mpesa/stk-push/v1', {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${secretKey}`, 'Content-Type': 'application/json' },
            body: JSON.stringify({
                amount: amount,
                phone_number: phone,
                redirect_url: 'https://worldbestsports.netlify.app/success.html',
                comment: `World Best Sports - ${package_type}`
            })
        });
        return { statusCode: 200, body: JSON.stringify({ message: 'STK Push sent! Check your phone and enter your M-Pesa PIN.' }) };
    } catch (error) {
        return { statusCode: 500, body: JSON.stringify({ message: 'Payment error. Please try again.' }) };
    }
};
