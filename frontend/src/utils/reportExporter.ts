import jsPDF from 'jspdf';
import autoTable, { UserOptions } from 'jspdf-autotable';
import { AnalysisResponse } from '../services/analysisService';

const brandPrimary = '#1E40AF';
const brandAccent = '#38BDF8';
const textDark = '#0F172A';
const textMuted = '#64748B';
const marginX = 48;
const topMargin = 48;
const bottomMargin = 64;
const sectionSpacing = 32;

const hexToRgb = (hex: string): [number, number, number] => {
  const clean = hex.replace('#', '');
  const bigint = parseInt(clean, 16);
  return [(bigint >> 16) & 255, (bigint >> 8) & 255, bigint & 255];
};

const ensureSpace = (doc: jsPDF, cursor: number, required = 120) => {
  const pageHeight = doc.internal.pageSize.getHeight();
  if (cursor + required > pageHeight - bottomMargin) {
    doc.addPage();
    return topMargin;
  }
  return cursor;
};

const getLastTableBottom = (doc: jsPDF) => {
  const last = (doc as unknown as { lastAutoTable?: { finalY?: number } }).lastAutoTable;
  if (last && typeof last.finalY === 'number') {
    return last.finalY;
  }
  return undefined;
};

const formatScore = (value: number) => `${Math.round(value)} / 100`;

const addCoverSection = (doc: jsPDF, result: AnalysisResponse) => {
  const width = doc.internal.pageSize.getWidth();

  doc.setFillColor(...hexToRgb(brandPrimary));
  doc.rect(0, 0, width, 180, 'F');

  doc.setFillColor(...hexToRgb(brandAccent));
  doc.circle(width - 120, 70, 55, 'F');
  doc.setFillColor(255, 255, 255);
  doc.circle(width - 70, 140, 42, 'F');

  doc.setFont('helvetica', 'bold');
  doc.setTextColor('#FFFFFF');
  doc.setFontSize(30);
  doc.text('Magentix Intelligence Report', marginX, 80);

  doc.setFont('helvetica', 'normal');
  doc.setFontSize(14);
  doc.text('Executive insights to accelerate revenue and conversion growth', marginX, 108);

  doc.setFontSize(12);
  doc.text(`Prepared for: ${result.metadata.requested_url}`, marginX, 132);
  doc.text(`Generated: ${new Date(result.metadata.timestamp).toLocaleString()}`, marginX, 148);

  const panelY = 200;
  const panelWidth = width - marginX * 2;

  const chips = [
    ['SEO Health', formatScore(result.seo_analysis.overall_score)],
    ['Conversion Strength', formatScore(result.conversion_analysis.overall_score)],
    ['Technical SEO', formatScore(result.seo_analysis.technical_seo)],
    ['Content Quality', formatScore(result.seo_analysis.content_quality)],
    ['Pages Analyzed', `${result.metadata.pages_analyzed}`],
  ];

  const chipWidth = 140;
  const chipHeight = 46;
  const chipGap = 16;
  const chipsPerRow = 3;
  const chipRows = Math.ceil(chips.length / chipsPerRow);
  const panelHeight = 60 + chipRows * (chipHeight + 12);

  doc.setFillColor(255, 255, 255);
  doc.roundedRect(marginX, panelY, panelWidth, panelHeight, 12, 12, 'F');
  doc.setDrawColor(226, 232, 240);
  doc.roundedRect(marginX, panelY, panelWidth, panelHeight, 12, 12, 'S');

  const overallScore = Math.round((result.seo_analysis.overall_score + result.conversion_analysis.overall_score) / 2);
  const grade = overallScore >= 90 ? 'A+' : overallScore >= 80 ? 'A' : overallScore >= 70 ? 'B' : overallScore >= 60 ? 'C' : overallScore >= 50 ? 'D' : 'F';

  doc.setFont('helvetica', 'bold');
  doc.setFontSize(48);
  doc.setTextColor(brandPrimary);
  doc.text(grade, marginX + 32, panelY + 62);

  doc.setFont('helvetica', 'normal');
  doc.setFontSize(12);
  doc.setTextColor(textMuted);
  doc.text('Overall performance grade', marginX + 32, panelY + 80);

  const chipStartX = marginX + 180;

  chips.forEach(([label, value], index) => {
    const row = Math.floor(index / chipsPerRow);
    const col = index % chipsPerRow;
    const chipX = chipStartX + col * (chipWidth + chipGap);
    const chipY = panelY + 30 + row * (chipHeight + 12);

    doc.setFillColor(248, 250, 252);
    doc.setDrawColor(226, 232, 240);
    doc.roundedRect(chipX, chipY, chipWidth, chipHeight, 10, 10, 'FD');

    doc.setFont('helvetica', 'bold');
    doc.setFontSize(12);
    doc.setTextColor(textDark);
    doc.text(value, chipX + 12, chipY + 22);

    doc.setFont('helvetica', 'normal');
    doc.setFontSize(10);
    doc.setTextColor(textMuted);
    doc.text(label, chipX + 12, chipY + 36);
  });

  return panelY + panelHeight + sectionSpacing;
};

const addScoreBreakdown = (doc: jsPDF, cursor: number, result: AnalysisResponse) => {
  const rows = [
    ['SEO Scores', 'Title Optimisation', formatScore(result.seo_analysis.title_optimization)],
    ['', 'Meta Descriptions', formatScore(result.seo_analysis.meta_description)],
    ['', 'Header Structure', formatScore(result.seo_analysis.header_structure)],
    ['', 'Internal Linking', formatScore(result.seo_analysis.internal_linking)],
    ['Conversion Scores', 'Headline Effectiveness', formatScore(result.conversion_analysis.headline_effectiveness)],
    ['', 'Value Proposition', formatScore(result.conversion_analysis.value_proposition)],
    ['', 'CTA Optimisation', formatScore(result.conversion_analysis.cta_optimization)],
    ['', 'Trust Signals', formatScore(result.conversion_analysis.trust_signals)],
    ['', 'Form Optimisation', formatScore(result.conversion_analysis.form_optimization ?? 0)],
    ['', 'Urgency & Scarcity', formatScore(result.conversion_analysis.urgency_scarcity)],
  ];

  const startY = ensureSpace(doc, cursor, 160);

  doc.setFont('helvetica', 'bold');
  doc.setFontSize(16);
  doc.setTextColor(textDark);
  doc.text('Detailed Score Breakdown', marginX, startY);

  autoTable(doc, {
    startY: startY + 16,
    head: [['Category', 'Metric', 'Result']],
    body: rows,
    styles: {
      fontSize: 10,
      cellPadding: 6,
      textColor: [15, 23, 42],
    },
    headStyles: {
      fillColor: hexToRgb(brandPrimary),
      textColor: [255, 255, 255],
      fontStyle: 'bold',
    },
    columnStyles: {
      0: { cellWidth: 140, fontStyle: 'bold', textColor: hexToRgb(brandPrimary) },
      2: { halign: 'right' },
    },
    willDrawCell: (data) => {
      if (data.section === 'body' && data.column.index === 0 && data.cell.raw === '') {
        data.cell.text = [''];
      }
    },
  } as UserOptions);

  return (getLastTableBottom(doc) ?? startY + 180) + sectionSpacing;
};

const addExecutiveSummary = (doc: jsPDF, cursor: number, result: AnalysisResponse) => {
  let startY = ensureSpace(doc, cursor, 120);

  doc.setFont('helvetica', 'bold');
  doc.setFontSize(16);
  doc.setTextColor(textDark);
  doc.text('Executive Summary', marginX, startY);

  doc.setFont('helvetica', 'normal');
  doc.setFontSize(11);
  doc.setTextColor(textMuted);

  const textWidth = doc.internal.pageSize.getWidth() - marginX * 2;
  const summaryLines = doc.splitTextToSize(result.summary || 'Summary not available.', textWidth);
  const lineHeight = 14;

  doc.text(summaryLines, marginX, startY + 18);

  const contentHeight = summaryLines.length * lineHeight;
  return startY + 18 + contentHeight + sectionSpacing;
};

const addRecommendations = (doc: jsPDF, cursor: number, result: AnalysisResponse) => {
  const recommendations = result.recommendations.slice(0, 12);
  let startY = ensureSpace(doc, cursor, recommendations.length ? 160 : 80);

  doc.setFont('helvetica', 'bold');
  doc.setFontSize(16);
  doc.setTextColor(textDark);
  doc.text('Strategic Recommendations', marginX, startY);

  if (recommendations.length === 0) {
    doc.setFont('helvetica', 'italic');
    doc.setFontSize(11);
    doc.setTextColor(textMuted);
    doc.text('No recommendations available.', marginX, startY + 18);
    return startY + 36;
  }

  const body = recommendations.map((rec, index) => [
    `#${index + 1}`,
    rec.priority,
    rec.category,
    rec.issue,
    rec.recommendation,
    rec.implementation,
  ]);

  autoTable(doc, {
    startY: startY + 18,
    head: [['', 'Priority', 'Focus', 'Issue', 'Recommendation', 'Implementation Guidance']],
    body,
    styles: {
      fontSize: 9,
      cellPadding: 5,
      valign: 'top',
    },
    headStyles: {
      fillColor: hexToRgb(brandPrimary),
      textColor: [255, 255, 255],
      fontStyle: 'bold',
    },
    columnStyles: {
      0: { cellWidth: 28 },
      1: { cellWidth: 66 },
      2: { cellWidth: 72 },
      3: { cellWidth: 120 },
      4: { cellWidth: 160 },
      5: { cellWidth: 'auto' },
    },
  } as UserOptions);

  return (getLastTableBottom(doc) ?? startY + 220) + sectionSpacing;
};

const addInsights = (doc: jsPDF, cursor: number, result: AnalysisResponse) => {
  let startY = ensureSpace(doc, cursor, 150);

  doc.setFont('helvetica', 'bold');
  doc.setFontSize(16);
  doc.setTextColor(textDark);
  doc.text('Key Insights & Opportunities', marginX, startY);

  const renderList = (title: string, items: string[], listStartY: number) => {
    if (!items || items.length === 0) {
      return listStartY;
    }

    const initialY = ensureSpace(doc, listStartY, 40);
    if (initialY !== listStartY) {
      doc.setFont('helvetica', 'bold');
      doc.setFontSize(16);
      doc.setTextColor(textDark);
      doc.text('Key Insights & Opportunities (cont.)', marginX, initialY);
      listStartY = initialY + 20;
    } else {
      listStartY = initialY;
    }

    doc.setFont('helvetica', 'bold');
    doc.setFontSize(12);
    doc.setTextColor(textDark);
    doc.text(title, marginX, listStartY);

    doc.setFont('helvetica', 'normal');
    doc.setFontSize(11);
    doc.setTextColor(textMuted);

    const textWidth = doc.internal.pageSize.getWidth() - marginX * 2 - 16;
    let cursorY = listStartY + 16;

    items.forEach((item, index) => {
      const ensuredY = ensureSpace(doc, cursorY, 20);
      if (ensuredY !== cursorY) {
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(16);
        doc.setTextColor(textDark);
        doc.text('Key Insights & Opportunities (cont.)', marginX, ensuredY);
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(12);
        doc.setTextColor(textDark);
        doc.text(title, marginX, ensuredY + 20);
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(11);
        doc.setTextColor(textMuted);
        cursorY = ensuredY + 36;
      } else {
        cursorY = ensuredY;
      }
      const paragraphs = doc.splitTextToSize(`${index + 1}. ${item}`, textWidth);
      doc.text(paragraphs, marginX + 10, cursorY);
      cursorY += paragraphs.length * 14;
    });

    return cursorY + 10;
  };

  let cursorY = startY + 20;
  cursorY = renderList('Competitive Insights', result.insights.competitive_insights || [], cursorY);
  cursorY = renderList('Content Gaps', result.insights.content_gaps || [], cursorY);
  cursorY = renderList('Technical Issues', result.technical_issues || [], cursorY);
  cursorY = renderList('High-Value SEO Keywords', result.insights.seo_keyword_insights || [], cursorY);
  cursorY = renderList('Conversion Highlights', result.insights.conversion_highlights || [], cursorY);

  return cursorY + sectionSpacing;
};

const addPagesSnapshot = (doc: jsPDF, cursor: number, result: AnalysisResponse) => {
  const pages = result.insights.pages_analyzed_details || [];
  if (pages.length === 0) {
    return cursor;
  }

  let startY = ensureSpace(doc, cursor, 160);

  doc.setFont('helvetica', 'bold');
  doc.setFontSize(16);
  doc.setTextColor(textDark);
  doc.text('Pages Analyzed Snapshot', marginX, startY);

  const body = pages.slice(0, 14).map((page, index) => [
    `#${index + 1}`,
    page.title || page.url,
    page.word_count ? `${page.word_count.toLocaleString()} words` : '—',
    page.load_time ? `${page.load_time}s` : '—',
  ]);

  autoTable(doc, {
    startY: startY + 18,
    head: [['', 'Page', 'Content Depth', 'Load Time']],
    body,
    styles: {
      fontSize: 9,
      cellPadding: 5,
    },
    headStyles: {
      fillColor: hexToRgb(brandPrimary),
      textColor: [255, 255, 255],
      fontStyle: 'bold',
    },
    columnStyles: {
      0: { cellWidth: 28 },
      1: { cellWidth: 260 },
      2: { cellWidth: 110 },
      3: { cellWidth: 90, halign: 'right' },
    },
  } as UserOptions);

  return (getLastTableBottom(doc) ?? startY + 200) + sectionSpacing;
};

const addFooter = (doc: jsPDF) => {
  const pageCount = doc.getNumberOfPages();
  for (let page = 1; page <= pageCount; page += 1) {
    doc.setPage(page);
    const width = doc.internal.pageSize.getWidth();
    const height = doc.internal.pageSize.getHeight();

    doc.setDrawColor(226, 232, 240);
    doc.line(marginX, height - bottomMargin, width - marginX, height - bottomMargin);

    doc.setFont('helvetica', 'normal');
    doc.setFontSize(10);
    doc.setTextColor(textMuted);
    doc.text('© Magentix • Intelligent Growth Partner', marginX, height - bottomMargin + 20);
    doc.text(`Page ${page} of ${pageCount}`, width - marginX - 80, height - bottomMargin + 20);
  }
};

export const exportAnalysisReport = (result: AnalysisResponse) => {
  const doc = new jsPDF({ orientation: 'portrait', unit: 'pt', format: 'letter' });

  let cursor = addCoverSection(doc, result);
  cursor = addScoreBreakdown(doc, cursor, result);
  cursor = addExecutiveSummary(doc, cursor, result);
  cursor = addRecommendations(doc, cursor, result);
  cursor = addInsights(doc, cursor, result);
  addPagesSnapshot(doc, cursor, result);
  addFooter(doc);

  const safeUrl = result.metadata.requested_url.replace(/https?:\/\//, '').replace(/\W+/g, '-');
  doc.save(`magentix-report-${safeUrl}.pdf`);
};
