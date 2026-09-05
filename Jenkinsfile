pipeline {
    agent any

    environment {
        PATH = "C:\\Users\\perfi\\Desktop\\study\\5\\WEB programming\\library\\.venv\\Scripts\\;${env.PATH}"
        DJANGO_SETTINGS_MODULE = 'library.settings'
        PYTHONUNBUFFERED = '1'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                echo 'Code checked out'
            }
        }

        stage('Setup') {
            steps {
                bat '''
                    python --version
                    pip install -r requirements.txt
                '''
            }
        }

        stage('Test') {
            steps {
                bat '''
                    python manage.py test --noinput
                '''
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
                echo 'Deploy to production'
            }
        }
    }

    post {
        success {
            echo 'Build succeeded'
        }
        failure {
            echo 'Build failed'
        }
    }
}