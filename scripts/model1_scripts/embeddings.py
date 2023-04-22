import torch
from transformers import BertTokenizer, BertModel
import numpy as np

OUTPUT_DIM = 768


class TitleEmbeddingModel():

    def __init__(self, base_model='bert-base-cased'):
        if torch.cuda.is_available():
            self.device = torch.device("cuda")
        else:
            self.device = torch.device("cpu")

        self.tokenizer = BertTokenizer.from_pretrained(base_model)

        self.model = BertModel.from_pretrained(base_model)
        self.model.to(self.device)

    def __call__(self, input, max_seq_length, batch_size=None):
        if batch_size is None:
            batch_size = len(input)

        index = 0
        output = torch.Tensor(np.zeros((len(input), OUTPUT_DIM))).to(self.device)
        while index < len(input):
            output[index:index+batch_size] = \
                self._create_embeddings(input[index:index+batch_size], max_seq_length)
            index += batch_size
                
        return output
    
    def _create_embeddings(self, input, max_seq_length):
        tokenized_input = self.tokenizer(text=input,
                                         add_special_tokens=True,
                                         padding='max_length',
                                         max_length=max_seq_length,
                                         return_tensors='pt',  # PyTorch tensors
                                         truncation=True,
                                         return_attention_mask=True)

        input_ids = tokenized_input['input_ids'].to(self.device)
        att_masks = tokenized_input['attention_mask'].to(self.device)

        with torch.no_grad():
            output = self.model(input_ids=input_ids, attention_mask=att_masks)[1]

        return output