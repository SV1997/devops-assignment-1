pipeline {
    agent any

    environment {
        IMAGE_NAME = 'accest-fitness'
        IMAGE_TAG = "${BUILD_NUMBER}"
        AWS_REGION = 'eu-north-1'
        AWS_ACCOUNT_ID = '525409063755'
        ECR_REPO = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/accest-fitness"
        EKS_CLUSTER_NAME = 'casual-bluegrass-gopher'
        PYTHON_EXE = 'C:\\Users\\saharsh vashishtha\\AppData\\Local\\Programs\\Python\\Python312\\python.exe'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Setup and Install') {
            steps {
                bat '''
                if exist venv rmdir /s /q venv
                "%PYTHON_EXE%" --version
                "%PYTHON_EXE%" -m venv venv
                venv\\Scripts\\python -m pip install --upgrade pip setuptools wheel
                venv\\Scripts\\python -m pip install -r requirements.txt
                venv\\Scripts\\python -m pip install pytest pytest-cov flake8
                '''
            }
        }

        stage('Lint') {
            steps {
                bat 'venv\\Scripts\\python -m flake8 .'
            }
        }

        stage('Test') {
            steps {
                bat 'venv\\Scripts\\python -m pytest --cov=. --cov-report=xml --cov-report=term'
            }
        }

        stage('Build Docker Image') {
            steps {
                bat '''
                docker build -t %IMAGE_NAME%:%IMAGE_TAG% .
                '''
            }
        }

        stage('Push Docker Image to ECR') {
            steps {
                withCredentials([[
                    $class: 'AmazonWebServicesCredentialsBinding',
                    credentialsId: 'aws-creds'
                ]]) {
                    bat '''
                    aws ecr get-login-password --region %AWS_REGION% | docker login --username AWS --password-stdin %AWS_ACCOUNT_ID%.dkr.ecr.%AWS_REGION%.amazonaws.com
                    docker tag %IMAGE_NAME%:%IMAGE_TAG% %ECR_REPO%:%IMAGE_TAG%
                    docker push %ECR_REPO%:%IMAGE_TAG%
                    '''
                }
            }
        }

        stage('Deploy to EKS') {
            steps {
                withCredentials([[
                    $class: 'AmazonWebServicesCredentialsBinding',
                    credentialsId: 'aws-creds'
                ]]) {
                    bat '''
                    aws eks update-kubeconfig --region %AWS_REGION% --name %EKS_CLUSTER_NAME%
                    kubectl config current-context
                    kubectl get deployment -n aceest
                    kubectl set image deployment/aceest-fitness aceest-fitness=%ECR_REPO%:%IMAGE_TAG% -n aceest
                    kubectl rollout status deployment/aceest-fitness -n aceest
                    '''
                }
            }
        }
    }
}