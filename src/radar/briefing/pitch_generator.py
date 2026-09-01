"""Pitch brief and client outreach email generator for BD team members."""

from typing import Any, Dict, List, Optional
from radar.models import Client, OpportunityRecord, ServiceLine


class PitchGenerator:
    """Generates personalized 1-page BD pitch briefs, talking points, and client outreach emails."""

    def generate_brief(
        self,
        opportunity: OpportunityRecord,
        client: Optional[Client] = None,
        service_line: Optional[ServiceLine] = None,
        contact_name: Optional[str] = None,
        custom_angle: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Produces a structured pitch brief with a formatted email draft and strategic talking points."""
        client_name = client.name if client else (opportunity.target_client_id or "Target Agency")
        service_line_name = service_line.name if service_line else (opportunity.primary_service_line_id or "Advisory Services")
        recipient = contact_name if contact_name else (opportunity.target_contact_persona or "Agency Leadership")

        # Determine salutation
        if contact_name:
            salutation_name = contact_name.strip()
            # If name has title like 'Dr. Sarah Jenkins' -> 'Dr. Jenkins' or use full name
            parts = salutation_name.split()
            if len(parts) >= 2 and parts[0].lower() in ("dr.", "dr", "hon.", "hon", "prof.", "prof", "mr.", "mr", "ms.", "ms"):
                salutation = f"{parts[0]} {parts[-1]}"
            elif len(parts) >= 2:
                salutation = salutation_name
            else:
                salutation = salutation_name
        else:
            salutation = recipient

        # 1. Build Email Draft
        subject = f"Allen + Clarke | Advisory Brief: {client_name} - {opportunity.title}"

        email_paragraphs = [
            f"Dear {salutation},",
            f"I hope this note finds you well. I am reaching out from Allen + Clarke regarding the recent developments concerning {opportunity.title}.",
        ]

        if opportunity.verified_facts:
            email_paragraphs.append(
                f"With the latest statutory directives indicating: \"{opportunity.verified_facts}\", we recognize that {client_name} may be assessing capacity and operational requirements to implement these mandates effectively."
            )

        if opportunity.strategic_interpretation:
            email_paragraphs.append(
                f"From our work supporting public sector leaders across {opportunity.jurisdiction}, we know that {opportunity.strategic_interpretation.lower() if opportunity.strategic_interpretation[0].isupper() else opportunity.strategic_interpretation}"
            )

        if custom_angle:
            email_paragraphs.append(
                f"In particular, regarding {custom_angle}, our practice brings dedicated expertise to assist your team in navigating these complex milestones."
            )

        # Service line and proof points
        if service_line:
            case_study_text = ""
            if service_line.case_studies:
                cs = service_line.case_studies[0]
                case_study_text = f" (for example, our recent work on '{cs.get('title')}')"
            email_paragraphs.append(
                f"Our {service_line_name} practice regularly partners with agencies on {service_line.description.lower()}{case_study_text}."
            )
        elif opportunity.conversation_starter:
            email_paragraphs.append(opportunity.conversation_starter)

        # Client past engagements reference
        if client and client.past_engagements:
            engagements_summary = ", ".join(client.past_engagements[:2])
            email_paragraphs.append(
                f"Building on Allen + Clarke's prior engagement with {client.name} around {engagements_summary}, we are well-positioned to deliver rapid, high-trust support."
            )

        # Call to action
        email_paragraphs.append(
            "Would you or your team have 20 minutes next week for an informal briefing to discuss our observations and how we might support your upcoming milestones?"
        )
        email_paragraphs.append(
            "Warm regards,\n\nBusiness Development Practice Lead\nAllen + Clarke Policy and Regulatory Specialists"
        )

        email_body = "\n\n".join(email_paragraphs)

        # 2. Build Talking Points
        talking_points: List[str] = []
        if opportunity.conversation_starter:
            talking_points.append(f"Conversation Opener: {opportunity.conversation_starter}")
        if opportunity.verified_facts:
            talking_points.append(f"Mandate & Trigger: {opportunity.verified_facts}")
        if opportunity.strategic_interpretation:
            talking_points.append(f"Strategic Pain Point: {opportunity.strategic_interpretation}")
        if service_line:
            talking_points.append(f"A+C Capability Alignment: Leverage our {service_line_name} service line.")
        if custom_angle:
            talking_points.append(f"Tailored Entry Angle: {custom_angle}")
        if client and client.relationship_notes:
            talking_points.append(f"Relationship Intelligence: {client.relationship_notes}")

        # 3. Recommended Next Steps
        recommended_next_steps = [
            f"1. Review target persona profile: {opportunity.target_contact_persona or 'Lead Decision Maker'}.",
            f"2. Send personalized outreach email to {recipient}.",
            f"3. Attach relevant Allen + Clarke {service_line_name} capability statement / case studies.",
            "4. Log outreach date and responses in client relationship registry.",
        ]

        # 4. Build 1-Page Markdown Brief
        md_lines = [
            f"# Executive BD Brief: {opportunity.title}",
            "",
            "## Opportunity Overview",
            f"- **Opportunity ID**: `{opportunity.id}`",
            f"- **Target Client**: **{client_name}** ({opportunity.jurisdiction})",
            f"- **Primary Service Line**: **{service_line_name}**",
            f"- **Priority Score**: **{opportunity.total_score}/100** (Strategic Fit: {opportunity.strategic_fit_score}/35, Urgency: {opportunity.urgency_score}/35, Budget: {opportunity.budget_score}/30)",
            f"- **Target Persona**: `{opportunity.target_contact_persona or 'Director / General Manager'}`",
            "",
            "## Policy Context & Strategic Assessment",
            f"### Verified Statutory Facts\n{opportunity.verified_facts or 'No statutory facts recorded.'}",
            "",
            f"### Strategic Consulting Interpretation\n{opportunity.strategic_interpretation or 'No strategic interpretation recorded.'}",
            "",
        ]

        if custom_angle:
            md_lines.extend([
                "## Custom Strategic Angle",
                f"> {custom_angle}",
                "",
            ])

        if client and (client.past_engagements or client.relationship_notes):
            md_lines.extend([
                "## Client Relationship Intelligence",
                f"- **Sector & Tier**: {client.sector} ({client.tier})",
                f"- **Past Engagements**: {', '.join(client.past_engagements) if client.past_engagements else 'None recorded'}",
                f"- **Relationship Notes**: {client.relationship_notes or 'None'}",
                "",
            ])

        md_lines.extend([
            "## Key BD Talking Points",
            "\n".join([f"- {tp}" for tp in talking_points]),
            "",
            "## Recommended BD Next Steps",
            "\n".join(recommended_next_steps),
            "",
            "## Ready-to-Send Outreach Email Draft",
            f"**Subject**: `{subject}`",
            f"**To**: `{recipient}`",
            "",
            "```text",
            email_body,
            "```",
        ])

        pitch_brief_markdown = "\n".join(md_lines)

        return {
            "opportunity_id": opportunity.id,
            "title": opportunity.title,
            "client_name": client_name,
            "service_line_name": service_line_name,
            "score": opportunity.total_score,
            "pitch_brief_markdown": pitch_brief_markdown,
            "email_draft": {
                "recipient": recipient,
                "subject": subject,
                "body": email_body,
            },
            "talking_points": talking_points,
            "recommended_next_steps": recommended_next_steps,
        }
