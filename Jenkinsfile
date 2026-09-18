pipeline {
    agent any

    environment {
        PATH = "C:\\Program Files\\nodejs\\;${env.PATH}"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                echo 'Code checked out'
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
                    def deployDir = "C:\\deploy\\frontend"
                    bat """
                        taskkill /F /IM python.exe 2>nul
                        taskkill /F /IM pythonw.exe 2>nul
                        timeout /t 3 /nobreak >nul
                        if exist "${deployDir}" rmdir /S /Q "${deployDir}"
                        timeout /t 2 /nobreak >nul
                        if exist "${deployDir}" rmdir /S /Q "${deployDir}"
                        mkdir "${deployDir}"
                        xcopy /E /I /Y "client\\dist" "${deployDir}\\"
                    """
                    echo "Фронтенд развернут в ${deployDir}"
                }
            }
        }

        stage('Run Frontend') {
            steps {
                script {
                    def pythonPath = "C:\\\\Users\\\\perfi\\\\Desktop\\\\study\\\\5\\\\WEB programming\\\\library\\\\.venv\\\\Scripts\\\\python.exe"
                    bat """
                        powershell -Command "Start-Process -FilePath '${pythonPath}' -ArgumentList '-m','http.server','4173' -WorkingDirectory 'C:\\\\deploy\\\\frontend' -WindowStyle Hidden"
                    """
                    echo "Фронтенд запущен на http://localhost:4173"
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