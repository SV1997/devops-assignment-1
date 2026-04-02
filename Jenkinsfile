pipeline {
    agent any

    environment {
        IMAGE_NAME = "aceest-fitness"
        IMAGE_TAG  = "${BUILD_NUMBER}"
    }

    stages {

        stage('Checkout') {
            steps {
                echo "Pulling latest code from GitHub..."
                checkout scm
            }
        }

        stage('Build Environment') {
            steps {
                echo "Setting up Python virtual environment..."
                sh '''
                    python3 -m venv venv
                    ./venv/bin/python -m pip install --upgrade pip
                    ./venv/bin/pip install -r requirements.txt
                '''
            }
        }

        stage('Lint') {
            steps {
                echo "Running flake8 syntax check..."
                sh '''
                    ./venv/bin/pip install flake8
                    ./venv/bin/flake8 app.py --select=E9,F63,F7,F82 --count --show-source --statistics
                '''
            }
        }

        stage('Unit Tests') {
            steps {
                echo "Running Pytest suite..."
                sh '''
                    ./venv/bin/pip install pytest pytest-cov
                    ./venv/bin/pytest test_app.py -v --tb=short --junitxml=test-results.xml
                '''
            }
            post {
                always {
                    junit 'test-results.xml'
                }
            }
        }

        stage('Docker Build') {
            steps {
                echo "Building Docker image..."
                sh 'docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .'
            }
        }

    }

    post {
        success {
            echo "BUILD SUCCEEDED - ACEest image is ready."
        }
        failure {
            echo "BUILD FAILED - check logs above for details."
        }
        always {
            cleanWs()
        }
    }
}