pipeline {
    agent any

    environment {
        IMAGE_NAME = "aceest-fitness"
        IMAGE_TAG  = "${BUILD_NUMBER}"
        PYTHON = "C:\\Users\\saharsh vashishtha\\AppData\\Local\\Programs\\Python\\Python310\\python.exe"
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
                bat """
                    "%PYTHON%" -m venv venv
                    venv\\Scripts\\python.exe -m pip install --upgrade pip
                    venv\\Scripts\\python.exe -m pip install -r requirements.txt
                """
            }
        }

        stage('Lint') {
            steps {
                echo "Running flake8 syntax check..."
                bat """
                    venv\\Scripts\\python.exe -m pip install flake8
                    venv\\Scripts\\flake8.exe app.py --select=E9,F63,F7,F82 --count --show-source --statistics
                """
            }
        }

        stage('Unit Tests') {
            steps {
                echo "Running Pytest suite..."
                bat """
                    venv\\Scripts\\python.exe -m pip install pytest pytest-cov
                    venv\\Scripts\\pytest.exe test_app.py -v --tb=short --junitxml=test-results.xml
                """
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
                bat "docker build -t %IMAGE_NAME%:%IMAGE_TAG% ."
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