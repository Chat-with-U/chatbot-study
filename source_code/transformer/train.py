from models import Transformer
from transformers import AdamW


from torch.utils.data import DataLoader
from torch import nn
import torch

from tqdm import tqdm


class Trainer(object):
    def __init__(self, dataset, batch_size, lr, epoch, device, vocab_size,
                 max_seq_len, handler, use_attention=True):
        self.dataset = dataset
        self.batch_size = batch_size
        self.lr = lr
        self.epoch = epoch
        self.device = device
        self.vocab_size = vocab_size
        self.max_seq_len = max_seq_len
        self.use_attention = use_attention
        self.model = Transformer(vocab_size, 1, 6, 512, 768)
        self.handler = handler

    def train(self):
        chichat_dataloader = DataLoader(self.dataset, batch_size=self.batch_size, shuffle=True)
        criterion = nn.CrossEntropyLoss()
        optimizer = AdamW(self.model.parameters(), self.lr)
        model = self.model.to(self.device)

        step = 0
        for epoch in tqdm(range(100)):
            for encode_input, decode_input in tqdm(chichat_dataloader):
                encode_input = encode_input.to(self.device)
                decode_input = decode_input.to(self.device)

                step += 1
                optimizer.zero_grad()

                projected_output = model(encode_input, decode_input)

                loss = 0
                for i in range(projected_output.size()[0]):
                    loss += criterion(projected_output[i][:len(decode_input[i])], decode_input[i])

                loss.backward()
                optimizer.step()

            if epoch % 10 == 0:
                sample_input = self.handler.decode_without_tag(encode_input[0][encode_input[0] != 0].tolist())
                sample_output = self.handler.decode_without_tag(
                    projected_output[0].argmax(-1)[projected_output[0].argmax(-1) != 0].tolist())
                print(f'loss: {loss}')
                print(f'input_sentence: {sample_input}')
                print(f'output_sentence: {sample_output}')
                checkpoiont = {
                    'model': model.state_dict()
                }

                torch.save(checkpoiont, 'checkpoiont.pt')

    def interact_with_chatbot(self, utterance):
        input_sentence = input('챗봇에게 말을 걸어보세요 : ')
        dummy_decode_input = self.make_sentence2input('').unsqueeze(0)
        model = self.model.to(self.device)

        input_tensor = self.make_sentence2input(input_sentence).unsqueeze(0)

        with torch.no_grad():
            dummy_decode_input = dummy_decode_input.to(self.device)
            input_tensor = input_tensor.to(self.device)

            logit = model(input_tensor, dummy_decode_input)
            sample_output = self.handler.decode_without_tag(logit[0].argmax(-1)[logit[0].argmax(-1) != 0].tolist())

        print(sample_output)

    def make_sentence2input(self, sentence):
        input_ids = self.handler.encode(sentence)
        if len(input_ids) + 2 < 60:
            padding_block = self.max_seq_len - len(input_ids) + 2
            input = torch.LongTensor([self.token2index['[START]']] +
                                     input_ids +
                                     [self.token2index['[END]']] +
                                     [self.token2index['[PAD]']] * padding_block)
        else:
            input = torch.LongTensor([self.token2index['[START]']] +
                                     input_ids +
                                     [self.token2index['[END]']])

        return input
