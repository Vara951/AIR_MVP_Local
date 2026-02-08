# llm_service.py - Improved Backend with Better Prompts
import os
from groq import Groq
from search_engine import HybridSearchEngine
from dotenv import load_dotenv

load_dotenv('.env')


class IncidentAnalyzer:
    """Handles search and LLM runbook generation"""

    def __init__(self):
        self.search_engine = HybridSearchEngine()
        self.groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))
        print("✅ Incident Analyzer initialized")

    def analyze_incident(self, description: str, tech_stack: str, error_message: str = None):
        """Main analysis function"""

        # Search similar incidents
        search_query = f"{description} {error_message or ''}"
        results = self.search_engine.search_similar(
            query=search_query,
            current_tech_stack=tech_stack,
            limit=10
        )

        # Generate analysis with Groq
        root_cause, solution, reasoning = self._generate_analysis(
            description=description,
            tech_stack=tech_stack,
            error_message=error_message,
            same_stack=results['same_stack'],
            cross_stack=results['cross_stack']
        )

        return {
            'same_stack': results['same_stack'][:5],
            'cross_stack': results['cross_stack'][:5],
            'root_cause': root_cause,
            'solution': solution,
            'reasoning': reasoning,
            'most_similar': results['same_stack'][0] if results['same_stack'] else results['cross_stack'][0] if results[
                'cross_stack'] else None
        }

    def _generate_analysis(self, description, tech_stack, error_message, same_stack, cross_stack):
        """Generate analysis using Groq - IMPROVED PROMPT"""

        # Format similar incidents
        same_stack_context = ""
        if same_stack:
            inc = same_stack[0]  # Most similar
            same_stack_context = f"""
MOST SIMILAR INCIDENT (Same Stack - {tech_stack}):
ID: {inc['id']}
Title: {inc['title']}
Root Cause: {inc['root_cause']}
Solution: {inc['solution'][0]}
"""

        cross_stack_context = ""
        if cross_stack:
            inc = cross_stack[0]  # Most similar from other stack
            cross_stack_context = f"""
CROSS-STACK INSIGHT ({inc['tech_stack']}):
ID: {inc['id']}
Title: {inc['title']}
Root Cause: {inc['root_cause']}
Solution: {inc['solution'][0]}
"""

        # Build STRICT prompt
        prompt = f"""You are a DevOps engineer analyzing a production incident. Use ONLY the provided similar incidents as reference. DO NOT make up information.

CURRENT INCIDENT:
Tech Stack: {tech_stack}
Description: {description}
Error: {error_message or 'Not provided'}

{same_stack_context}

{cross_stack_context}

STRICT INSTRUCTIONS:
1. Identify the MOST LIKELY root cause based on similar incidents above
2. Provide a 5-step solution adapted to {tech_stack}
3. Explain why similar incidents apply
4. Use ONLY information from the incidents above
5. If no similar incidents exist, say "Insufficient data - manual investigation required"

Format EXACTLY as:

ROOT CAUSE:
[Single paragraph explaining the most likely root cause based on similar incidents]

SOLUTION:
1. [Immediate action - 5 min]
2. [Investigation step - 10 min]
3. [Fix implementation - 15 min]
4. [Verification - 5 min]
5. [Prevention - 10 min]

REASONING:
[Explain why the similar incident's solution applies to this {tech_stack} case. Focus on shared root cause, not syntax.]
"""

        try:
            completion = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a precise DevOps engineer. Base your analysis ONLY on provided incidents. Never hallucinate. If insufficient data, say so clearly."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,  # Lower temperature = less hallucination
                max_tokens=1500
            )

            response_text = completion.choices[0].message.content

            # Parse response
            root_cause = "Unable to determine"
            solution = "Manual investigation required"
            reasoning = "Insufficient similar incidents found"

            if "ROOT CAUSE:" in response_text:
                parts = response_text.split("SOLUTION:")
                root_cause = parts[0].replace("ROOT CAUSE:", "").strip()

                if len(parts) > 1:
                    solution_parts = parts[1].split("REASONING:")
                    solution = solution_parts[0].strip()

                    if len(solution_parts) > 1:
                        reasoning = solution_parts[1].strip()

            return root_cause, solution, reasoning

        except Exception as e:
            return f"Error: {str(e)}", "LLM call failed", "Check API key"

    def _format_incidents(self, incidents):
        """Format incidents for display"""
        return "\n\n".join([
            f"**{inc['id']}** [{inc['tech_stack']}]: {inc['title']}\n"
            f"Root Cause: {inc['root_cause'][:120]}\n"
            f"Solution: {inc['solution'][0]}"
            for inc in incidents
        ])
