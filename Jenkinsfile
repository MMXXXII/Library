pipeline {
    agent any

    environment {
        PATH = "C:\\Users\\perfi\\Desktop\\study\\5\\WEB programming\\library\\.venv\\Scripts\\;C:\\Program Files\\nodejs\\;${env.PATH}"
        DJANGO_SETTINGS_MODULE = 'app.settings'
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
            when { branch 'main' }
            steps {
                script {
                    def deployDir = "C:\\deploy\\library-app"
                    bat """
                        if not exist "${deployDir}" mkdir "${deployDir}"
                        xcopy /E /I /Y "client\\dist" "${deployDir}\\frontend"
                        xcopy /E /I /Y "app" "${deployDir}\\backend"
                    """
                    echo "Приложение развернуто в ${deployDir}"
                }
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