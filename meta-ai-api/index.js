const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

// Read credentials
const credentialsPath = path.join(__dirname, '..', 'credentials.json');
const credentials = JSON.parse(fs.readFileSync(credentialsPath, 'utf8'));

async function generateResponse(prompt) {
    const browser = await puppeteer.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    try {
        const page = await browser.newPage();

        // Set cookie for authentication
        await page.setCookie({
            name: 'c_user',
            value: credentials.META_AI.cookie,
            domain: '.facebook.com'
        });

        // Navigate to Meta AI
        await page.goto('https://www.facebook.com/ai');
        await page.waitForSelector('textarea[aria-label="Message Meta AI"]');

        // Type prompt and send
        await page.type('textarea[aria-label="Message Meta AI"]', prompt);
        await page.keyboard.press('Enter');

        // Wait for response
        await page.waitForSelector('.x1lliihq'); // Response message class
        
        // Get the latest response
        const response = await page.evaluate(() => {
            const messages = document.querySelectorAll('.x1lliihq');
            return messages[messages.length - 1].textContent;
        });

        return response;
    } catch (error) {
        console.error('Error:', error);
        return null;
    } finally {
        await browser.close();
    }
}

// Handle command line arguments
const prompt = process.argv[2];
if (prompt) {
    generateResponse(prompt)
        .then(response => {
            if (response) {
                console.log(response);
                process.exit(0);
            } else {
                console.error('Failed to generate response');
                process.exit(1);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            process.exit(1);
        });
} else {
    console.error('Please provide a prompt');
    process.exit(1);
}
