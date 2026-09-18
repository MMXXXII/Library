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

        stage('Collect Static') {
            steps {
                bat '''
                    python manage.py collectstatic --noinput
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
            steps {
                script {
                    def deployDir = "C:\\deploy\\library-app"
                    bat """
                        if exist "${deployDir}" rmdir /S /Q "${deployDir}"
                        mkdir "${deployDir}"
                        xcopy /E /I /Y "manage.py" "${deployDir}\\"
                        xcopy /E /I /Y "requirements.txt" "${deployDir}\\"
                        xcopy /E /I /Y "db.sqlite3" "${deployDir}\\"
                        xcopy /E /I /Y "app" "${deployDir}\\app"
                        xcopy /E /I /Y "library" "${deployDir}\\library"
                        if exist "templates" xcopy /E /I /Y "templates" "${deployDir}\\templates"
                        if exist "media" xcopy /E /I /Y "media" "${deployDir}\\media"
                        if exist "staticfiles" xcopy /E /I /Y "staticfiles" "${deployDir}\\staticfiles"
                        if exist "client\\dist" xcopy /E /I /Y "client\\dist" "${deployDir}\\frontend"
                    """
                    echo "Приложение развернуто в ${deployDir}"
                }
            }
        }

        stage('Run Backend') {
            steps {
                script {
                    def deployDir = "C:\\deploy\\library-app"
                    bat """
                        taskkill /F /IM python.exe /FI "WINDOWTITLE eq LibraryApp*" 2>nul
                        timeout /t 2 /nobreak >nul
                        cd /d "${deployDir}"
                        start "LibraryApp" cmd /c "python manage.py runserver 0.0.0.0:8000"
                    """
                    echo "Бэкенд запущен на http://localhost:8000"
                }
            }
        }

        stage('Start Nginx') {
            steps {
                bat '''
                    taskkill /F /IM nginx.exe 2>nul
                    timeout /t 2 /nobreak >nul
                    cd /d C:\\Users\\perfi\\Downloads\\nginx-1.28.3
                    start nginx
                '''
                echo "Nginx запущен на http://localhost"
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