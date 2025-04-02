# from flask import Flask, render_template, request, redirect, url_for
# from fakenews import predict_news, store_feedback, retrain_model_with_feedback
# from flask_apscheduler import APScheduler
# import os
# from waitress import serve

# # Render-specific configuration
# PORT = int(os.environ.get('PORT', 10000))  

# app = Flask(__name__)

# # ------------------------------
# # Scheduler Configuration
# # ------------------------------
# class Config:
#     SCHEDULER_API_ENABLED = True

# app.config.from_object(Config())

# scheduler = APScheduler()
# scheduler.init_app(app)
# scheduler.start()

# # Define a scheduled job to retrain the model every 2 hours
# @scheduler.task('interval', id='retrain_job', hours=2)
# def scheduled_retrain():
#     print("Scheduled retraining started...")
#     retrain_model_with_feedback()
#     print("Scheduled retraining complete.")

# # ------------------------------
# # Flask Routes
# # ------------------------------
# # Force port binding verification
# import socket
# sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# sock.bind(('0.0.0.0', PORT))
# sock.close()

# @app.route('/')
# def index():
#     return render_template('index.html')

# @app.route('/predict', methods=['POST'])
# def predict():
#     news_text = request.form['news_text']
#     result = predict_news(news_text)
#     # Pass the news_text and predicted verdict as query parameters for feedback
#     return render_template('index.html', result=result, news_text=news_text, predicted_verdict=result["verdict"])

# @app.route('/feedback', methods=['GET', 'POST'])
# def feedback():
#     if request.method == 'POST':
#         news_text = request.form['news_text']
#         predicted_verdict = request.form['predicted_verdict']
#         correct_label = request.form['correct_label']
#         feedback_details = request.form['feedback_details']
#         # Store feedback in the database (score is set to 0 by default here)
#         store_feedback(news_text, predicted_verdict, correct_label, feedback_details, score=0)
#         return redirect(url_for('index'))
#     else:
#         news_text = request.args.get('news_text', '')
#         predicted_verdict = request.args.get('predicted_verdict', '')
#         return render_template('feedback.html', news_text=news_text, predicted_verdict=predicted_verdict)

# # You can also create a manual retrain route if desired:
# @app.route('/retrain', methods=['GET'])
# def retrain():
#     retrain_model_with_feedback()
#     return "Model retrained with feedback data.", 200

# # At the very bottom of app.py
# if __name__ == '__main__':
#     # DEVELOPMENT ONLY - Remove for production
#     app.run(debug=False, host='0.0.0.0', port=PORT)
# else:
#     # Production configuration
#     from waitress import serve
#     print(f"🚀 Production server starting on port {PORT}")
#     serve(app, host='0.0.0.0', port=PORT)





import os
from flask import Flask, render_template, request, redirect, url_for
from fakenews import predict_news, store_feedback, retrain_model_with_feedback
from flask_apscheduler import APScheduler
from waitress import serve

# Configuration for Render
PORT = int(os.environ.get('PORT', 10000))
app = Flask(__name__)

# ------------------------------
# Suppress TensorFlow warnings
# ------------------------------
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 
import tensorflow as tf
tf.get_logger().setLevel('ERROR')

# ------------------------------
# Scheduler Configuration
# ------------------------------
class Config:
    SCHEDULER_API_ENABLED = True
    SCHEDULER_TIMEZONE = "UTC"

app.config.from_object(Config())
scheduler = APScheduler()

# ------------------------------
# Routes & Core Functionality
# ------------------------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    news_text = request.form['news_text']
    result = predict_news(news_text)
    return render_template('index.html', 
                         result=result,
                         news_text=news_text,
                         predicted_verdict=result["verdict"])

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        store_feedback(
            request.form['news_text'],
            request.form['predicted_verdict'],
            request.form['correct_label'],
            request.form['feedback_details'],
            score=0
        )
        return redirect(url_for('index'))
    return render_template('feedback.html',
                         news_text=request.args.get('news_text', ''),
                         predicted_verdict=request.args.get('predicted_verdict', ''))

@app.route('/retrain')
def retrain():
    retrain_model_with_feedback()
    return "Model retrained with feedback data.", 200

@app.route('/ping')
def health_check():
    return "OK", 200

# ------------------------------
# Production Server Setup
# ------------------------------
def start_server():
    print(f"🚀 Server started on port {PORT}")
    print(f"🔗 Local: http://localhost:{PORT}")
    print(f"🌐 Network: http://0.0.0.0:{PORT}")
    
    # Verify port binding
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('0.0.0.0', PORT))
    except socket.error as e:
        print(f"❌ Port binding failed: {e}")
        exit(1)

if __name__ == '__main__':
    # Development mode
    start_server()
    app.run(host='0.0.0.0', port=PORT, debug=False)
else:
    # Production mode (Render)
    start_server()
    serve(app, host='0.0.0.0', port=PORT, threads=4)