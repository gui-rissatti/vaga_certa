import jsPDF from 'jspdf';
import type { ParsedCv } from '../types';

// --- Layout Constants ---
const MARGIN = { top: 12, left: 12, right: 12, bottom: 12 };
const FONT_SIZES = {
  name: 18,
  header: 10,
  subheader: 9.5,
  body: 9.5,
  contact: 8.5,
};
const LINE_HEIGHT_RATIO = 1.3;
const FONT = 'Helvetica';
const FONT_COLOR = '#1e293b'; // A dark slate, softer than pure black

export const generateCvPdf = async (cvData: ParsedCv): Promise<void> => {
    const doc = new jsPDF({
        orientation: 'portrait',
        unit: 'mm',
        format: 'a4',
    });

    let y = MARGIN.top;
    const pageWidth = doc.internal.pageSize.getWidth();
    const contentWidth = pageWidth - MARGIN.left - MARGIN.right;

    doc.setTextColor(FONT_COLOR);

    // --- Helper to add a new page if content overflows ---
    const checkAndAddPage = () => {
        if (y > doc.internal.pageSize.getHeight() - MARGIN.bottom) {
            doc.addPage();
            y = MARGIN.top;
        }
    };
    
    // --- Name ---
    doc.setFont(FONT, 'bold');
    doc.setFontSize(FONT_SIZES.name);
    const name = (cvData.name || 'Unnamed').toString();
    doc.text(name, pageWidth / 2, y, { align: 'center' });
    y += 7;

    // --- Contact Info ---
    doc.setFont(FONT, 'normal');
    doc.setFontSize(FONT_SIZES.contact);
    const contactInfo = [
        cvData.contact.address,
        cvData.contact.phone,
        cvData.contact.email,
        cvData.contact.linkedin,
    ].filter(Boolean).join('  •  ') || 'Contact information not provided';
    doc.text(contactInfo.toString(), pageWidth / 2, y, { align: 'center' });
    y += 10;

    // --- Section Renderer ---
    const renderSection = (title: string, renderContent: () => void) => {
        checkAndAddPage();
        doc.setFont(FONT, 'bold');
        doc.setFontSize(FONT_SIZES.header);
        doc.text((title || '').toString().toUpperCase(), MARGIN.left, y);
        y += 1.5;
        doc.setLineWidth(0.3);
        doc.line(MARGIN.left, y, pageWidth - MARGIN.right, y);
        y += 5;
        doc.setFont(FONT, 'normal');
        doc.setFontSize(FONT_SIZES.body);
        renderContent();
        y += 6;
    };

    // --- Summary ---
    if (cvData.summary) {
        renderSection('Summary', () => {
            const summaryLines = doc.splitTextToSize(cvData.summary, contentWidth);
            doc.text(summaryLines, MARGIN.left, y, { lineHeightFactor: LINE_HEIGHT_RATIO });
            y += summaryLines.length * FONT_SIZES.body / 2.5 * LINE_HEIGHT_RATIO;
        });
    }

    // --- Experience ---
    if (cvData.experience?.length > 0) {
        renderSection('Experience', () => {
            cvData.experience.forEach(exp => {
                checkAndAddPage();
                doc.setFont(FONT, 'bold');
                doc.text((exp.role || 'Role not specified').toString(), MARGIN.left, y);
                doc.setFont(FONT, 'normal');
                doc.text((exp.period || '').toString(), pageWidth - MARGIN.right, y, { align: 'right' });
                y += FONT_SIZES.body / 2 * LINE_HEIGHT_RATIO;

                doc.setFont(FONT, 'italic');
                doc.text((exp.company || 'Company not specified').toString(), MARGIN.left, y);
                y += 4;
                doc.setFont(FONT, 'normal');

                exp.responsibilities.forEach(resp => {
                    checkAndAddPage();
                    const bulletPoint = '•';
                    const bulletWidth = doc.getTextWidth(bulletPoint + ' ');
                    const textLines = doc.splitTextToSize(resp, contentWidth - bulletWidth - 2);
                    doc.text(bulletPoint, MARGIN.left + 2, y, { lineHeightFactor: LINE_HEIGHT_RATIO });
                    doc.text(textLines, MARGIN.left + 2 + bulletWidth, y, { lineHeightFactor: LINE_HEIGHT_RATIO });
                    y += textLines.length * FONT_SIZES.body / 2.5 * LINE_HEIGHT_RATIO + 0.8;
                });
                y += 3;
            });
        });
    }

    // --- Education ---
    if (cvData.education?.length > 0) {
        renderSection('Education', () => {
             cvData.education.forEach(edu => {
                checkAndAddPage();
                doc.setFont(FONT, 'bold');
                doc.text((edu.degree || 'Degree not specified').toString(), MARGIN.left, y);
                doc.setFont(FONT, 'normal');
                doc.text((edu.period || '').toString(), pageWidth - MARGIN.right, y, { align: 'right' });
                y += FONT_SIZES.body / 2 * LINE_HEIGHT_RATIO;

                doc.setFont(FONT, 'italic');
                doc.text((edu.institution || 'Institution not specified').toString(), MARGIN.left, y);
                y += 6;
            });
        });
    }

    // --- Skills ---
    if (cvData.skills?.length > 0) {
        renderSection('Skills', () => {
            const skillsText = cvData.skills.join('  •  ');
            const skillLines = doc.splitTextToSize(skillsText, contentWidth);
            doc.text(skillLines, MARGIN.left, y, { lineHeightFactor: LINE_HEIGHT_RATIO });
            y += skillLines.length * FONT_SIZES.body / 2.5 * LINE_HEIGHT_RATIO;
        });
    }

    const safeName = (cvData.name || 'Resume').toString().replace(/\s+/g, '_');
    const filename = `${safeName}_Resume.pdf`;
    doc.save(filename);
};