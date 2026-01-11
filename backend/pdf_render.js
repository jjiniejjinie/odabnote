#!/usr/bin/env node
/**
 * PDF 생성 스크립트 (Puppeteer + KaTeX)
 * 사용법: node pdf_render.js <html_path> <output_path>
 */

const puppeteer = require('puppeteer');
const fs = require('fs');

async function generatePDF(htmlPath, outputPath) {
    console.log('Starting PDF generation...');
    console.log(`HTML: ${htmlPath}`);
    console.log(`Output: ${outputPath}`);
    
    // HTML 파일 존재 확인
    if (!fs.existsSync(htmlPath)) {
        console.error(`HTML file not found: ${htmlPath}`);
        process.exit(1);
    }
    
    let browser;
    try {
        // Puppeteer 브라우저 시작
        browser = await puppeteer.launch({
            headless: 'new',
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-software-rasterizer',
                '--disable-extensions'
            ],
            executablePath: process.env.PUPPETEER_EXECUTABLE_PATH || puppeteer.executablePath()
        });
        
        console.log('Browser launched');
        
        const page = await browser.newPage();
        
        // HTML 로드
        const htmlContent = fs.readFileSync(htmlPath, 'utf8');
        await page.setContent(htmlContent, {
            waitUntil: 'networkidle0'
        });
        
        console.log('HTML loaded');
        
        // 폰트 로딩 완료 대기
        await page.evaluate(() => document.fonts.ready);
        console.log('Fonts loaded');
        
        // KaTeX 렌더링 완료 대기 (추가 시간)
        await page.waitForTimeout(2000);
        console.log('KaTeX rendered');
        
        // PDF 생성
        await page.pdf({
            path: outputPath,
            format: 'A4',
            printBackground: true,
            margin: {
                top: '10mm',
                bottom: '15mm',
                left: '10mm',
                right: '10mm'
            }
        });
        
        console.log('PDF generated successfully!');
        
    } catch (error) {
        console.error('Error generating PDF:', error);
        process.exit(1);
    } finally {
        if (browser) {
            await browser.close();
        }
    }
}

// 커맨드라인 인자 처리
const args = process.argv.slice(2);

if (args.length !== 2) {
    console.error('Usage: node pdf_render.js <html_path> <output_path>');
    process.exit(1);
}

const [htmlPath, outputPath] = args;

generatePDF(htmlPath, outputPath)
    .then(() => {
        console.log('Done!');
        process.exit(0);
    })
    .catch((error) => {
        console.error('Fatal error:', error);
        process.exit(1);
    });
