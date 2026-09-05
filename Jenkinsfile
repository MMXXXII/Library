pipeline {
    agent any

    environment {
        DJANGO_SETTINGS_MODULE = 'library.settings'
        PYTHONUNBUFFERED = '1'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                echo 'Код получен из репозитория'
            }
        }

        stage('Backend Setup') {
            steps {
                dir('app') {
                    bat '''
                        python -m venv venv
                        venv\\Scripts\\activate
                        pip install -r requirements.txt
                    '''
                }
            }
        }

        stage('Run Tests') {
            steps {
                dir('app') {
                    bat '''
                        venv\\Scripts\\activate
                        python manage.py test --noinput
                    '''
                }
            }
        }

        stage('Build Frontend') {
            steps {
                dir('client') {
                    bat '''
                        npm install
                        npm run build
                    '''
                }
            }
        }

        stage('Deploy') {
            when {
                branch 'main'
            }
            steps {
                echo 'Развертывание на продакшн (заглушка)'
            }
        }
    }

    post {
        success {
            echo 'CI/CD Pipeline выполнен успешно!'
        }
        failure {
            echo 'Pipeline завершился с ошибкой!'
        }
    }
}