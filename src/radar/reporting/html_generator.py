"""HTML Email Digest Generator for Allen + Clarke Fortnightly Opportunity Radar."""

import html
from typing import Any, Dict, List, Optional, Union
from radar.pipeline.models import BDOpportunity
from radar.reporting.models import ReportMetadata


class HTMLReportGenerator:
    """Renders responsive, email-ready HTML briefing cards for Allen + Clarke BD radar."""

    def generate_email_digest(
        self,
        opportunities: List[BDOpportunity],
        title: Optional[str] = None,
        metadata: Optional[Union[Dict[str, Any], ReportMetadata]] = None,
    ) -> str:
        """Generates an executive-grade, responsive HTML email digest.

        Args:
            opportunities: List of prioritized BDOpportunity instances.
            title: Optional custom digest title.
            metadata: Optional dictionary or ReportMetadata instance.
        """
        meta = ReportMetadata.from_dict(metadata)
        digest_title = title or "Allen + Clarke BD Opportunity Radar"
        scanned_count = meta.scanned_count if meta.scanned_count > 0 else len(opportunities)

        opp_count = len(opportunities)
        high_priority_count = sum(1 for o in opportunities if o.score.total_score >= 80)

        # Build cards HTML
        cards_html = ""
        if not opportunities:
            cards_html = """
            <div class="empty-state">
                <div class="empty-icon">&#128269;</div>
                <h3>No high-scoring opportunities identified</h3>
                <p>All ingested policy feeds in this scan cycle were either filtered as ceremonial/administrative noise or scored below actionable consulting thresholds.</p>
            </div>
            """
        else:
            cards = []
            for idx, opp in enumerate(opportunities, start=1):
                total = opp.score.total_score
                fit = opp.score.strategic_fit_score
                urgency = opp.score.urgency_score
                budget = opp.score.budget_score

                # Score color coding
                if total >= 80:
                    score_bg = "#059669"
                    score_label = "HIGH PRIORITY"
                elif total >= 65:
                    score_bg = "#d97706"
                    score_label = "MEDIUM PRIORITY"
                else:
                    score_bg = "#64748b"
                    score_label = "MONITOR"

                # Jurisdiction badge
                jur_bg = "#2563eb" if opp.jurisdiction == "NZ" else "#7c3aed"

                # Obligations HTML
                obligations_html = "".join([f"<li>{html.escape(o)}</li>" for o in opp.operational_obligations])
                deadlines_html = "".join([f"<span class=\"deadline-badge\">&#9200; {html.escape(d)}</span>" for d in opp.compliance_deadlines])
                pitch_angles_html = "".join([f"<li>{html.escape(a)}</li>" for a in opp.key_pitch_angles])

                card = f"""
                <div class="opportunity-card">
                    <div class="card-header">
                        <div class="card-badges">
                            <span class="rank-badge">#{idx}</span>
                            <span class="jurisdiction-badge" style="background-color: {jur_bg};">{html.escape(opp.jurisdiction)}</span>
                            <span class="service-badge">{html.escape(opp.service_line_name)}</span>
                        </div>
                        <div class="score-badge-container">
                            <span class="score-label" style="color: {score_bg};">{score_label}</span>
                            <div class="score-pill" style="background-color: {score_bg};">{total}<span class="score-max">/100</span></div>
                        </div>
                    </div>

                    <h2 class="card-title"><a href="{html.escape(opp.url)}" target="_blank">{html.escape(opp.title)}</a></h2>

                    <div class="client-meta">
                        <strong>Target Client:</strong> <span class="client-name">{html.escape(opp.target_client_name)}</span> &bull; 
                        <strong>Published:</strong> {html.escape(opp.published_date)}
                    </div>

                    <!-- Score Breakdown Bar -->
                    <div class="score-breakdown">
                        <div class="score-metric">
                            <span class="metric-name">Strategic Fit</span>
                            <div class="metric-bar-bg"><div class="metric-bar-fill" style="width: {int((fit / 35) * 100)}%; background-color: #3b82f6;"></div></div>
                            <span class="metric-val">{fit}/35</span>
                        </div>
                        <div class="score-metric">
                            <span class="metric-name">Statutory Urgency</span>
                            <div class="metric-bar-bg"><div class="metric-bar-fill" style="width: {int((urgency / 35) * 100)}%; background-color: #ef4444;"></div></div>
                            <span class="metric-val">{urgency}/35</span>
                        </div>
                        <div class="score-metric">
                            <span class="metric-name">Budget Likelihood</span>
                            <div class="metric-bar-bg"><div class="metric-bar-fill" style="width: {int((budget / 30) * 100)}%; background-color: #10b981;"></div></div>
                            <span class="metric-val">{budget}/30</span>
                        </div>
                    </div>

                    <!-- Change Summary -->
                    <div class="section-block">
                        <div class="section-title">&#128227; Policy Shift / Regulatory Change</div>
                        <p class="summary-text">{html.escape(opp.change_summary)}</p>
                    </div>

                    <!-- Fact vs Strategic Interpretation Comparison -->
                    <div class="demarcation-grid">
                        <div class="fact-box">
                            <div class="box-header fact-header">&#9989; Verified Statutory Facts</div>
                            <div class="box-body">{html.escape(opp.verified_facts)}</div>
                        </div>
                        <div class="interpretation-box">
                            <div class="box-header interpretation-header">&#128161; Strategic Consulting Interpretation</div>
                            <div class="box-body">{html.escape(opp.strategic_interpretation)}</div>
                        </div>
                    </div>

                    <!-- Operational Obligations & Deadlines -->
                    <div class="section-block obligations-block">
                        <div class="section-title">&#128203; Implementation Obligations & Compliance Deadlines</div>
                        <ul class="clean-list">
                            {obligations_html}
                        </ul>
                        {f'<div class="deadlines-container">{deadlines_html}</div>' if deadlines_html else ''}
                    </div>

                    <!-- A+C Service Line Offering Alignment -->
                    <div class="section-block service-offering-block">
                        <div class="section-title">&#128188; A+C Capability Alignment: {html.escape(opp.service_line_name)}</div>
                        <p class="summary-text">{html.escape(opp.service_offering_summary)}</p>
                    </div>

                    <!-- BD Action Plan Box -->
                    <div class="action-plan-box">
                        <div class="action-header">&#127919; Business Development Action Plan</div>
                        <div class="action-content">
                            <div class="persona-row">
                                <strong>Target Contact Persona:</strong> <code>{html.escape(opp.target_contact_persona)}</code>
                            </div>
                            <div class="starter-row">
                                <strong>Conversation Starter:</strong>
                                <blockquote class="starter-quote">"{html.escape(opp.conversation_starter)}"</blockquote>
                            </div>
                            <div class="angles-row">
                                <strong>Key Pitch Angles:</strong>
                                <ul class="pitch-list">
                                    {pitch_angles_html}
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
                """
                cards.append(card)
            cards_html = "\n".join(cards)

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(digest_title)} - {html.escape(meta.period)}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background-color: #f1f5f9;
            color: #1e293b;
            margin: 0;
            padding: 24px 12px;
            line-height: 1.5;
        }}
        .container {{
            max-width: 840px;
            margin: 0 auto;
            background: #ffffff;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
            border: 1px solid #e2e8f0;
        }}
        .header {{
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            color: #ffffff;
            padding: 32px 28px;
            border-bottom: 4px solid #0ea5e9;
        }}
        .header-brand {{
            font-size: 13px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            color: #38bdf8;
            margin-bottom: 8px;
        }}
        .header-title {{
            font-size: 26px;
            font-weight: 800;
            margin: 0 0 8px 0;
            letter-spacing: -0.5px;
        }}
        .header-meta {{
            font-size: 14px;
            color: #94a3b8;
        }}
        .stats-bar {{
            display: flex;
            background: #f8fafc;
            border-bottom: 1px solid #e2e8f0;
            padding: 16px 28px;
            gap: 24px;
            flex-wrap: wrap;
        }}
        .stat-item {{
            flex: 1;
            min-width: 140px;
        }}
        .stat-val {{
            font-size: 22px;
            font-weight: 800;
            color: #0f172a;
        }}
        .stat-label {{
            font-size: 12px;
            color: #64748b;
            text-transform: uppercase;
            font-weight: 600;
            letter-spacing: 0.5px;
        }}
        .content {{
            padding: 28px;
        }}
        .opportunity-card {{
            background: #ffffff;
            border: 1px solid #cbd5e1;
            border-radius: 10px;
            padding: 24px;
            margin-bottom: 28px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04);
            transition: transform 0.15s ease;
        }}
        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 14px;
            flex-wrap: wrap;
            gap: 10px;
        }}
        .card-badges {{
            display: flex;
            gap: 8px;
            align-items: center;
            flex-wrap: wrap;
        }}
        .rank-badge {{
            background: #0f172a;
            color: #ffffff;
            font-weight: 800;
            font-size: 12px;
            padding: 4px 10px;
            border-radius: 20px;
        }}
        .jurisdiction-badge {{
            color: #ffffff;
            font-weight: 700;
            font-size: 12px;
            padding: 4px 10px;
            border-radius: 20px;
        }}
        .service-badge {{
            background: #f1f5f9;
            color: #334155;
            font-weight: 600;
            font-size: 12px;
            padding: 4px 10px;
            border-radius: 20px;
            border: 1px solid #cbd5e1;
        }}
        .score-badge-container {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .score-label {{
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .score-pill {{
            color: #ffffff;
            font-weight: 800;
            font-size: 18px;
            padding: 4px 12px;
            border-radius: 8px;
            display: inline-flex;
            align-items: baseline;
        }}
        .score-max {{
            font-size: 12px;
            font-weight: 500;
            opacity: 0.85;
            margin-left: 2px;
        }}
        .card-title {{
            font-size: 20px;
            font-weight: 700;
            margin: 0 0 8px 0;
            line-height: 1.35;
        }}
        .card-title a {{
            color: #0f172a;
            text-decoration: none;
        }}
        .card-title a:hover {{
            color: #0284c7;
            text-decoration: underline;
        }}
        .client-meta {{
            font-size: 13px;
            color: #64748b;
            margin-bottom: 18px;
        }}
        .client-name {{
            color: #0f172a;
            font-weight: 600;
        }}
        .score-breakdown {{
            display: flex;
            gap: 16px;
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 12px 16px;
            margin-bottom: 18px;
            flex-wrap: wrap;
        }}
        .score-metric {{
            flex: 1;
            min-width: 120px;
        }}
        .metric-name {{
            font-size: 11px;
            color: #64748b;
            display: block;
            margin-bottom: 4px;
            font-weight: 600;
        }}
        .metric-bar-bg {{
            height: 6px;
            background: #e2e8f0;
            border-radius: 3px;
            overflow: hidden;
            margin-bottom: 4px;
        }}
        .metric-bar-fill {{
            height: 100%;
            border-radius: 3px;
        }}
        .metric-val {{
            font-size: 12px;
            font-weight: 700;
            color: #334155;
        }}
        .section-block {{
            margin-bottom: 16px;
        }}
        .service-offering-block {{
            background: #f0fdf4;
            border: 1px solid #bbf7d0;
            border-radius: 8px;
            padding: 12px 16px;
        }}
        .service-offering-block .section-title {{
            color: #166534;
            font-size: 12px;
        }}
        .section-title {{
            font-size: 13px;
            font-weight: 700;
            color: #334155;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 6px;
        }}
        .summary-text {{
            font-size: 14px;
            color: #334155;
            margin: 0;
            line-height: 1.5;
        }}
        .demarcation-grid {{
            display: flex;
            gap: 14px;
            margin-bottom: 18px;
            flex-wrap: wrap;
        }}
        .fact-box, .interpretation-box {{
            flex: 1;
            min-width: 280px;
            border-radius: 8px;
            overflow: hidden;
            font-size: 13px;
            line-height: 1.45;
        }}
        .fact-box {{
            border: 1px solid #bfdbfe;
            background: #eff6ff;
        }}
        .fact-header {{
            background: #dbeafe;
            color: #1e40af;
            font-weight: 700;
            padding: 8px 12px;
            font-size: 12px;
        }}
        .interpretation-box {{
            border: 1px solid #ddd6fe;
            background: #faf5ff;
        }}
        .interpretation-header {{
            background: #ede9fe;
            color: #5b21b6;
            font-weight: 700;
            padding: 8px 12px;
            font-size: 12px;
        }}
        .box-body {{
            padding: 12px;
            color: #1e293b;
        }}
        .clean-list {{
            margin: 0 0 10px 0;
            padding-left: 20px;
            font-size: 13px;
            color: #334155;
        }}
        .deadlines-container {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            margin-top: 8px;
        }}
        .deadline-badge {{
            background: #fee2e2;
            color: #991b1b;
            font-size: 11px;
            font-weight: 700;
            padding: 3px 8px;
            border-radius: 6px;
            border: 1px solid #fecaca;
        }}
        .action-plan-box {{
            background: #fdf4ff;
            border: 1px solid #f0abfc;
            border-radius: 8px;
            padding: 16px;
            margin-top: 18px;
        }}
        .action-header {{
            font-size: 13px;
            font-weight: 800;
            color: #86198f;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 10px;
        }}
        .persona-row {{
            font-size: 13px;
            color: #334155;
            margin-bottom: 8px;
        }}
        .persona-row code {{
            background: #ffffff;
            padding: 2px 6px;
            border-radius: 4px;
            border: 1px solid #e2e8f0;
            font-weight: 600;
            color: #701a75;
        }}
        .starter-row {{
            font-size: 13px;
            color: #334155;
            margin-bottom: 8px;
        }}
        .starter-quote {{
            margin: 6px 0 0 0;
            padding: 8px 12px;
            background: #ffffff;
            border-left: 3px solid #c026d3;
            font-style: italic;
            color: #4a044e;
            border-radius: 0 6px 6px 0;
        }}
        .pitch-list {{
            margin: 6px 0 0 0;
            padding-left: 20px;
            font-size: 13px;
            color: #334155;
        }}
        .empty-state {{
            text-align: center;
            padding: 48px 24px;
            color: #64748b;
        }}
        .empty-icon {{
            font-size: 40px;
            margin-bottom: 12px;
        }}
        .footer {{
            background: #f8fafc;
            border-top: 1px solid #e2e8f0;
            padding: 24px 28px;
            font-size: 12px;
            color: #64748b;
            text-align: center;
            line-height: 1.6;
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <div class="header-brand">Allen + Clarke Consulting</div>
            <h1 class="header-title">&#128065;&#65039; {html.escape(digest_title)}</h1>
            <div class="header-meta">
                <strong>Period:</strong> {html.escape(meta.period)} &bull; 
                <strong>Jurisdictions:</strong> {html.escape(meta.jurisdiction)} ({html.escape(meta.jurisdiction_label)}) &bull; 
                <strong>Generated:</strong> {html.escape(meta.generated_at)}
            </div>
        </div>

        <!-- Executive Metrics Bar -->
        <div class="stats-bar">
            <div class="stat-item">
                <div class="stat-val">{opp_count}</div>
                <div class="stat-label">Qualified Opportunities</div>
            </div>
            <div class="stat-item">
                <div class="stat-val" style="color: #059669;">{high_priority_count}</div>
                <div class="stat-label">High Priority (Score &ge; 80)</div>
            </div>
            <div class="stat-item">
                <div class="stat-val">{scanned_count}</div>
                <div class="stat-label">Total Items Ingested</div>
            </div>
        </div>

        <!-- Main Content -->
        <div class="content">
            {cards_html}
        </div>

        <!-- Footer -->
        <div class="footer">
            <p><strong>Allen + Clarke BD Opportunity Radar</strong> &bull; Policy, Evaluation & Strategic Advisory</p>
            <p>Auckland &bull; Wellington &bull; Melbourne &bull; Canberra</p>
            <p style="font-size: 11px; color: #94a3b8; margin-top: 8px;">Confidential — Distributed internally for Business Development & Practice Leadership.</p>
        </div>
    </div>
</body>
</html>"""

        return html_content
