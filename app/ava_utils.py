def ava_to_customvision_format(predictions):
    results = []
    for prediction in predictions:
        tagName = prediction['entity']['tag']['value']
        probability = float(prediction['entity']['tag']['confidence'])
        boundingBox = {
            "left": float(prediction['entity']['box']['l']),
            "top": float(prediction['entity']['box']['t']),
            "width": float(prediction['entity']['box']['w']),
            "height": float(prediction['entity']['box']['h']),
        }
        results.append(
            {
                "tagName": tagName,
                "probability": probability,
                "boundingBox": boundingBox,
            }
        )
    return(results)
