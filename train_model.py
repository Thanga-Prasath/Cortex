from core.nlu import NeuralIntentModel

if __name__ == "__main__":
    print("Initializing and Training NLU Model...")
    # The class processes data and trains automatically on init
    model = NeuralIntentModel()
    print("Training Complete. Model is ready.")
