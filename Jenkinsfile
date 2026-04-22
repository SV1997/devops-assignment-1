pipeline {
    agent any
    environment {
        APP_NAME = 'aceest-fitness'
        IMAGE_REPO = 'saharshvashishtha/aceest-fitness'
        IMAGE_TAG = "${BUILD_NUMBER}"
        SONARQUBE_ENV = 'sonarqube-server'
        K8S_NAMESPACE = 'aceest'
    }
    stages {
        stage('Checkout') { steps { checkout scm } }
        stage('Setup Python Environment') {
            steps {
                script {
                    if (isUnix()) {
                        sh '''
                            python3 -m venv venv
                            . venv/bin/activate
                            pip install --upgrade pip
                            pip install -r requirements.txt
                            pip install flake8 pytest pytest-cov
                        '''
                    } else {
                        bat '''
                            py -3 -m venv venv
                            call venv\Scripts\activate
                            python -m pip install --upgrade pip
                            pip install -r requirements.txt
                            pip install flake8 pytest pytest-cov
                        '''
                    }
                }
            }
        }
        stage('Lint') {
            steps {
                script {
                    if (isUnix()) {
                        sh '. venv/bin/activate && flake8 app.py test_app.py --count --show-source --statistics'
                    } else {
                        bat 'call venv\\Scripts\\activate && flake8 app.py test_app.py --count --show-source --statistics'
                    }
                }
            }
        }
        stage('Unit Tests') {
            steps {
                script {
                    if (isUnix()) {
                        sh '. venv/bin/activate && pytest test_app.py -v --tb=short --junitxml=test-results.xml --cov=app --cov-report=xml --cov-report=term'
                    } else {
                        bat 'call venv\\Scripts\\activate && pytest test_app.py -v --tb=short --junitxml=test-results.xml --cov=app --cov-report=xml --cov-report=term'
                    }
                }
            }
            post { always { junit 'test-results.xml' } }
        }
        stage('SonarQube Analysis') {
            steps {
                script {
                    def scannerHome = tool 'sonar-scanner'
                    withSonarQubeEnv("${SONARQUBE_ENV}") {
                        if (isUnix()) {
                            sh "${scannerHome}/bin/sonar-scanner"
                        } else {
                            bat "${scannerHome}\\bin\\sonar-scanner.bat"
                        }
                    }
                }
            }
        }
        stage('Quality Gate') {
            steps {
                timeout(time: 10, unit: 'MINUTES') { waitForQualityGate abortPipeline: true }
            }
        }
        stage('Docker Build') {
            steps {
                script { docker.build("${IMAGE_REPO}:${IMAGE_TAG}") }
            }
        }
        stage('Docker Push') {
            steps {
                script {
                    docker.withRegistry('https://index.docker.io/v1/', 'dockerhub-creds') {
                        def image = docker.image("${IMAGE_REPO}:${IMAGE_TAG}")
                        image.push()
                        image.push('latest')
                    }
                }
            }
        }
        stage('Deploy to Kubernetes') {
            steps {
                script {
                    if (isUnix()) {
                        sh '''
                            kubectl apply -f k8s/base/namespace.yaml
                            sed "s|IMAGE_PLACEHOLDER|${IMAGE_REPO}:${IMAGE_TAG}|g" k8s/base/deployment.yaml | kubectl apply -f -
                            kubectl apply -f k8s/base/service.yaml
                            kubectl rollout status deployment/aceest-fitness -n ${K8S_NAMESPACE} --timeout=120s
                        '''
                    } else {
                        bat '''
                            kubectl apply -f k8s/base/namespace.yaml
                            powershell -Command "(Get-Content k8s/base/deployment.yaml) -replace 'IMAGE_PLACEHOLDER','%IMAGE_REPO%:%IMAGE_TAG%' | kubectl apply -f -"
                            kubectl apply -f k8s/base/service.yaml
                            kubectl rollout status deployment/aceest-fitness -n %K8S_NAMESPACE% --timeout=120s
                        '''
                    }
                }
            }
        }
    }
    post {
        failure {
            script {
                try {
                    if (isUnix()) { sh 'kubectl rollout undo deployment/aceest-fitness -n ${K8S_NAMESPACE} || true' }
                    else { bat 'kubectl rollout undo deployment/aceest-fitness -n %K8S_NAMESPACE%' }
                } catch (exc) { echo "Rollback skipped: ${exc}" }
            }
        }
        always { cleanWs() }
    }
}
