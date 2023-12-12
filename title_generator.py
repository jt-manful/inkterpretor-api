# from transformers import AutoTokenizer, T5ForConditionalGeneration


from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

def title_generator(input_text):
    tokenizer = AutoTokenizer.from_pretrained("TusharJoshi89/title-generator")
    model = AutoModelForSeq2SeqLM.from_pretrained("TusharJoshi89/title-generator")

    input_ids = tokenizer(input_text, return_tensors="pt").input_ids

    outputs = model.generate(input_ids)
    summary = tokenizer.decode(outputs[0], skip_special_tokens=True)

    return summary




