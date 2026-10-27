grep -RnlE 'InferenceSession|InferenceSessionOptions|model.execute|session.execute' artifacts/v1.168-max --include='*.py' | head -25
