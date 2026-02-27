/**
 * HSM Test Framework - Jenkins Multi-Platform Pipeline
 *
 * Runs UI tests on Windows agent and console tests on Linux agent in parallel.
 * Collects evidence from both and publishes unified Allure report.
 *
 * Prerequisites:
 *   Windows agent (label: windows): Python 3.9+, Allure CLI, HSM app
 *   Linux agent (label: linux):     Python 3.9+, Allure CLI, PKCS#11 tools
 */

pipeline {
    agent none  // Agents assigned per stage

    parameters {
        choice(
            name: 'TEST_SUITE',
            choices: ['smoke', 'regression', 'all', 'ui', 'console', 'pkcs11'],
            description: 'Which test suite to run'
        )
        booleanParam(
            name: 'RUN_WINDOWS',
            defaultValue: true,
            description: 'Run Windows UI tests'
        )
        booleanParam(
            name: 'RUN_LINUX',
            defaultValue: true,
            description: 'Run Linux console/PKCS11 tests'
        )
    }

    environment {
        // Kiwi TCMS credentials (configure in Jenkins Credentials)
        // Comment out if not yet configured to avoid build errors
        // TCMS_API_URL  = credentials('tcms-api-url')
        // TCMS_USERNAME = credentials('tcms-username')
        // TCMS_PASSWORD = credentials('tcms-password')
        DUMMY = "placeholder"
    }

    options {
        timeout(time: 30, unit: 'MINUTES')
        timestamps()
        buildDiscarder(logRotator(numToKeepStr: '30'))
    }

    stages {
        stage('Test - Parallel') {
            parallel {
                // ============================================================
                // Windows Agent: UI Tests + Console Tests
                // ============================================================
                stage('Windows') {
                    when {
                        expression { params.RUN_WINDOWS }
                    }
                    agent { label 'windows' }
                    environment {
                        PYTHONPATH = "${WORKSPACE}"
                    }
                    stages {
                        stage('Win - Setup') {
                            steps {
                                bat '''
                                    python -m venv venv
                                    call venv\\Scripts\\activate.bat
                                    pip install --upgrade pip
                                    pip install -r requirements.txt
                                '''
                            }
                        }
                        stage('Win - Run Tests') {
                            steps {
                                script {
                                    def suite = params.TEST_SUITE
                                    def marker = (suite == 'all') ? '' : "-m ${suite}"
                                    bat """
                                        call venv\\Scripts\\activate.bat
                                        python -m pytest --smoke-gate ${marker} ^
                                            -v ^
                                            --tb=short ^
                                            --alluredir=evidence\\allure-results ^
                                            --junitxml=evidence\\junit-results-win.xml ^
                                            --timeout=120 ^
                                            2>&1 || exit /b 0
                                    """
                                }
                            }
                        }
                        stage('Win - Collect') {
                            steps {
                                archiveArtifacts(
                                    artifacts: 'evidence/**/*',
                                    allowEmptyArchive: true,
                                    fingerprint: true
                                )
                                junit(
                                    testResults: 'evidence/junit-results-win.xml',
                                    allowEmptyResults: true
                                )
                                stash(
                                    name: 'win-allure',
                                    includes: 'evidence/allure-results/**',
                                    allowEmpty: true
                                )
                            }
                        }
                    }
                }

                // ============================================================
                // Linux Agent: Console/PKCS11 Tests
                // ============================================================
                stage('Linux') {
                    when {
                        expression { params.RUN_LINUX }
                    }
                    agent { label 'linux' }
                    environment {
                        PYTHONPATH = "${WORKSPACE}"
                    }
                    stages {
                        stage('Linux - Setup') {
                            steps {
                                sh '''
                                    python3 -m venv venv
                                    . venv/bin/activate
                                    pip install --upgrade pip
                                    pip install -r requirements.txt
                                '''
                            }
                        }
                        stage('Linux - Run Tests') {
                            steps {
                                script {
                                    def suite = params.TEST_SUITE
                                    // On Linux: if suite is 'all' or 'ui', run all
                                    // (UI tests auto-skip via conftest platform guard)
                                    def marker = (suite == 'all') ? '' : "-m ${suite}"
                                    sh """
                                        . venv/bin/activate
                                        python3 -m pytest --smoke-gate ${marker} \
                                            -v \
                                            --tb=short \
                                            --alluredir=evidence/allure-results \
                                            --junitxml=evidence/junit-results-linux.xml \
                                            --timeout=120 \
                                            || true
                                    """
                                }
                            }
                        }
                        stage('Linux - Collect') {
                            steps {
                                archiveArtifacts(
                                    artifacts: 'evidence/**/*',
                                    allowEmptyArchive: true,
                                    fingerprint: true
                                )
                                junit(
                                    testResults: 'evidence/junit-results-linux.xml',
                                    allowEmptyResults: true
                                )
                                stash(
                                    name: 'linux-allure',
                                    includes: 'evidence/allure-results/**',
                                    allowEmpty: true
                                )
                            }
                        }
                    }
                }
            }
        }

        // ============================================================
        // Unified Allure Report (merge results from both platforms)
        // ============================================================
        stage('Allure Report') {
            agent { label 'windows || linux' }
            steps {
                // Unstash results from both platforms
                script {
                    try { unstash 'win-allure' } catch (e) { echo "No Windows results: ${e}" }
                    try { unstash 'linux-allure' } catch (e) { echo "No Linux results: ${e}" }
                }
                allure([
                    results: [[path: 'evidence/allure-results']]
                ])
            }
        }
    }

    post {
        always {
            echo "Build result: ${currentBuild.result ?: 'SUCCESS'}"
        }
        failure {
            echo 'Tests failed! Check Allure report and evidence artifacts.'
        }
    }
}
