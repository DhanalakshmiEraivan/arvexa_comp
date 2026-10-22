from django.core.management.base import BaseCommand
from arena.models import Question

DATA = [
    (1, 1, 'A classifier has 99% accuracy on a dataset where 99% of cases are negative. Which metric is most informative for detecting whether it is actually finding the rare positive cases?', ['Accuracy', 'Recall / sensitivity', 'Mean squared error', 'Training loss'], 'B'),
    (1, 2, 'A language model is evaluated on examples drawn from the same source as its training data and scores exceptionally high, but performance collapses on a new domain. Which failure is most directly demonstrated?', ['Data leakage only', 'Distribution shift with weak generalization', 'Gradient explosion', 'Under-parameterization'], 'B'),
    (1, 3, 'Which statement best distinguishes calibration from discrimination in probabilistic classification?', ['Calibration measures ranking; discrimination measures probability correctness', 'Calibration measures probability reliability; discrimination measures separation of classes', 'They are mathematically identical', 'Calibration is only relevant to regression'], 'B'),
    (1, 4, "A model's validation error is lowest at epoch 17 and rises afterward while training error keeps falling. What is the most defensible intervention?", ['Increase epochs indefinitely', 'Select the epoch near the validation minimum or use early stopping', 'Remove the validation set', 'Increase label noise'], 'B'),
    (1, 5, 'In a retrieval-augmented generation system, the retrieved passages are relevant but the final answer cites facts absent from them. Which component is the most direct source of the unsupported claim?', ['Retriever only', 'Generator / language model', 'Embedding index only', 'Tokenizer'], 'B'),
    (1, 6, 'Why can a high-dimensional nearest-neighbor model degrade as dimensionality increases even when more features are added?', ['All distances become exactly zero', 'Distance concentration can make neighborhoods less discriminative', 'Gradient descent stops working', 'Labels automatically become balanced'], 'B'),
    (1, 7, 'A model performs well offline but fails after deployment because the input distribution changed while the target relationship remained stable. What type of shift best describes this?', ['Covariate shift', 'Label leakage', 'Target encoding', 'Concept collapse'], 'A'),
    (1, 8, 'For a binary classifier with a fixed ranking of examples, lowering the decision threshold generally causes what change?', ['Recall tends to increase while precision may decrease', 'Both precision and recall must decrease', 'Recall must decrease while precision increases', 'The ROC curve changes because the model weights changed'], 'A'),
    (1, 9, 'A training pipeline accidentally includes a feature computed using information available only after the prediction event. The model scores brilliantly offline. What is this primarily?', ['Regularization', 'Target leakage', 'Class weighting', 'Quantization'], 'B'),
    (1, 10, 'Which statement about differential privacy is most accurate?', ['It guarantees zero information leakage', "It bounds how much the output distribution can change when one individual's data is added or removed", 'It encrypts every model parameter', 'It makes a model unbiased by definition'], 'B'),
    (1, 11, 'A transformer uses self-attention. For a sequence of length n and hidden width d, ignoring implementation optimizations, which scaling most directly explains the quadratic attention bottleneck in n?', ['O(d^2)', 'O(n)', 'O(n^2 d)', 'O(log n)'], 'C'),
    (1, 12, 'A generative model produces convincing samples but repeatedly omits a minority mode present in the training distribution. Which phenomenon is most closely described?', ['Mode collapse / mode dropping', 'Vanishing labels', 'Calibration gain', 'Stratified sampling'], 'A'),
    (1, 13, 'An experiment reports a statistically significant improvement after testing 80 metrics and highlighting only the smallest p-value. What is the core methodological concern?', ['Feature scaling', 'Multiple comparisons / selective reporting', 'Underfitting', 'Cross-validation leakage'], 'B'),
    (1, 14, 'In causal inference, why can conditioning on a collider create a spurious association between two otherwise independent causes?', ['It blocks every causal path', 'It opens a non-causal path through the common effect', 'It guarantees randomization', 'It converts correlation into intervention'], 'B'),
    (1, 15, "A model's loss is invariant to adding a constant to every logit before softmax. What property explains this?", ['Softmax is translation-invariant over logits', 'Softmax is scale-invariant over logits', 'Cross-entropy ignores labels', 'ReLU removes constants'], 'A'),
    (2, 16, 'A sequence follows a hidden rule: 2, 6, 12, 20, 30, 42, ?. What is the next term?', ['54', '56', '58', '60'], 'B'),
    (2, 17, 'Five machines produce 5 components in 5 minutes at identical rates. How many minutes do 100 machines need to produce 100 components?', ['5', '20', '100', '500'], 'A'),
    (2, 18, 'A two-digit integer is 4 times the sum of its digits. Reversing its digits increases it by 18. Which integer is it?', ['24', '36', '42', '48'], 'A'),
    (2, 19, 'If x + 1/x = 3 for nonzero x, what is x^2 + 1/x^2?', ['5', '7', '9', '11'], 'B'),
    (2, 20, 'Three boxes are labeled Red, Blue and Mixed, and every label is wrong. You may draw one ball from one box without looking inside. From which box must you draw to correctly relabel all three?', ['Red', 'Blue', 'Mixed', 'Any box'], 'C'),
    (2, 21, 'A clock gains 5 minutes every hour. It is set correctly at 12:00 noon. What time will it display when the actual time is 6:00 pm?', ['6:05 pm', '6:20 pm', '6:30 pm', '6:35 pm'], 'C'),
    (2, 22, 'In a class, 60% study A, 45% study B, and 25% study both. What percentage study neither A nor B?', ['10%', '20%', '25%', '30%'], 'B'),
    (2, 23, 'A fair coin is tossed 6 times. What is the probability of exactly four heads?', ['5/32', '15/64', '3/16', '1/4'], 'B'),
    (2, 24, 'A 3×3×3 cube is painted on every exterior face and cut into 27 unit cubes. How many unit cubes have exactly two painted faces?', ['8', '12', '16', '24'], 'B'),
    (2, 25, 'Find the smallest positive integer n such that n leaves remainder 2 when divided by 5, remainder 3 when divided by 7, and remainder 4 when divided by 9.', ['47', '67', '157', '292'], 'B'),
    (2, 26, 'A and B can complete a task together in 12 days. A alone takes 20 days. How many days would B alone take?', ['24', '28', '30', '32'], 'C'),
    (2, 27, 'If the roots of t² − kt + 12 = 0 differ by 2, which value of k is possible?', ['6', '7', '8', '10'], 'C'),
    (2, 28, 'A bag contains 5 red, 4 blue and 3 green balls. Two are drawn without replacement. What is the probability both are different colors?', ['47/66', '19/33', '1/2', '7/11'], 'A'),
    (2, 29, 'Four people P, Q, R and S sit in a row. P is not at an end. Q sits immediately to the left of R. S is not next to P. Which arrangement is possible?', ['P Q R S', 'Q R P S', 'S P Q R', 'Q P R S'], 'C'),
    (2, 30, 'A number is increased by 20% and then decreased by 20%. Compared with the original, the final value is:', ['Unchanged', '4% lower', '4% higher', '8% lower'], 'B'),
    (2, 31, 'The average of 8 numbers is 15. If one number is removed, the average of the remaining 7 is 13. What number was removed?', ['21', '27', '29', '31'], 'C'),
    (2, 32, 'A reservoir is filled by pipe A in 6 hours and emptied by pipe B in 9 hours. If both are opened together, how long to fill the reservoir?', ['12 hours', '15 hours', '18 hours', '54 hours'], 'C'),
    (2, 33, 'If 3^x = 81 and 2^y = 32, what is x + y?', ['8', '9', '10', '11'], 'B'),
    (2, 34, 'A 5-digit number uses five distinct digits from 1–9. How many such numbers are divisible by 5?', ['1,680', '2,016', '2,688', '3,024'], 'A'),
    (2, 35, 'A train 180 m long passes a pole in 9 seconds and a platform in 21 seconds. What is the platform length?', ['180 m', '210 m', '240 m', '260 m'], 'C'),
    (2, 36, 'If the ratio of boys to girls is 5:7 and 8 girls join, the ratio becomes 5:8. How many students were originally in the group?', ['72', '84', '96', '108'], 'C'),
    (2, 37, 'A sequence is defined by a₁=2 and aₙ₊₁=3aₙ−1. What is a₄?', ['38', '40', '41', '44'], 'C'),
    (2, 38, 'A rectangle has integer side lengths and area 96. Which perimeter is impossible?', ['40', '44', '50', '64'], 'C'),
    (2, 39, 'Exactly one of four statements P, Q, R, S is true. If P implies Q, and Q implies R, which statement cannot be true?', ['P', 'Q', 'R', 'S'], 'A'),
    (2, 40, 'A 4×4 grid of unit squares is drawn. How many total squares of all sizes are present?', ['16', '25', '30', '40'], 'C'),
]

class Command(BaseCommand):
    help = "Load the 40 final ARVEXA APTIQ questions."

    def handle(self, *args, **kwargs):
        Question.objects.all().delete()
        Question.objects.bulk_create([
            Question(round=rnd, order=order, prompt=prompt, a=opts[0], b=opts[1], c=opts[2], d=opts[3], correct=correct)
            for rnd, order, prompt, opts, correct in DATA
        ])
        self.stdout.write(self.style.SUCCESS("Loaded 40 unique advanced APTIQ questions."))
