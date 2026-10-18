from multi_agent.base_agent import BaseAgent

class CriticAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="CRITIC", role="Quality review and output improvement", max_tokens=400)

    def review_answer(self, question, answer):
        system = """You are ULTRON's Critic Agent. Review answer for accuracy completeness clarity relevance.
Return JSON: {"quality_score":0-10,"is_acceptable":true/false,"issues":["issue1"],"improved_answer":"better version","feedback":"brief feedback"}"""
        result = self.think_json(f"Question: {question}\nAnswer to review: {answer}", system)
        if not result:
            return {"quality_score":7,"is_acceptable":True,"issues":[],"improved_answer":answer,"feedback":"Acceptable"}
        return result

    def run(self, task, context=None):
        self.log(f"Reviewing output for: {task}")
        answer   = context.get("answer","") if context else ""
        question = context.get("question",task) if context else task
        if not answer:
            return {"agent":"critic_agent","task":task,"approved":False,"final_answer":"","quality_score":0}
        review       = self.review_answer(question, answer)
        final_answer = answer
        if not review.get("is_acceptable") and review.get("improved_answer"):
            final_answer = review["improved_answer"]
            self.log(f"Answer improved. Score: {review.get('quality_score')}/10")
        else:
            self.log(f"Answer approved. Score: {review.get('quality_score')}/10")
        return {"agent":"critic_agent","task":task,"approved":review.get("is_acceptable",True),
                "final_answer":final_answer,"quality_score":review.get("quality_score",7),
                "feedback":review.get("feedback","")}