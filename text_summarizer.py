from transformers import AutoTokenizer, PegasusForConditionalGeneration
import warnings


def text_summarizer(ARTICLE_TO_SUMMARIZE):
        
    # Suppress the warning
    warnings.filterwarnings("ignore", category=UserWarning, module="transformers.modeling_utils")

    model_name = "google/pegasus-large"
    model = PegasusForConditionalGeneration.from_pretrained(model_name)
    tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=False)
   
  
    inputs = tokenizer(ARTICLE_TO_SUMMARIZE, max_length=1024, return_tensors="pt", truncation=True)

    # Generate a summary
    summary_ids = model.generate(inputs["input_ids"])
    summary = tokenizer.batch_decode(summary_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0]

    return summary



# if __name__ =="__main__":
#     text_to_sum =  "Nokia will slash up to 14,000 jobs in a major cost-cutting drive to address a 'weaker' market environment, it said in a statement on Thursday. The Finnish telecom giant, a major provider of 5G equipment that employs 86,000 people, announced the move as part of a wider restructuring that will lower its headcount to between 72,000 and 77,000. The move will help the company reduce staffing expenses by 10% to 15%, and save at least €400 million ($421.4 million) in 2024 alone, the company projected. Overall, it said the reductions are expected to trim Nokia’s costs by up to €1.2 billion (nearly $1.3 billion) cumulatively by the end of 2026. Nokia (NOK) said it would 'act quickly' to make changes. 'The most difficult business decisions to make are the ones that impact our people,' CEO Pekka Lundmark said in the statement. 'We have immensely talented employees at Nokia and we will support everyone that is affected by this process.'"
#     print(text_summarizer(text_to_sum))