document.addEventListener("DOMContentLoaded", () => {

    // ==============================
    // AUDIO UPLOAD
    // ==============================

    const uploadButton = document.getElementById("upload-audio");
    const audioFileInput = document.getElementById("audio-file");
    const audioFileName = document.getElementById("audio-file-name");
    const audioDuration =
        document.getElementById("audio-duration");

    uploadButton.addEventListener("click", () => {
        audioFileInput.click();
    });

    audioFileInput.addEventListener("change", () => {

        const file = audioFileInput.files[0];

        if (!file) {
            return;
        }

        // Update file name
        audioFileName.textContent = file.name;

        // Read audio duration
        const audio = new Audio();

        audio.src = URL.createObjectURL(file);

        audio.addEventListener("loadedmetadata", () => {

            const duration = audio.duration;

            const minutes =
                Math.floor(duration / 60);

            const seconds =
                Math.floor(duration % 60);

            const formattedDuration =
                `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;

            if (audioDuration) {

                audioDuration.textContent =
                    `00:00 / ${formattedDuration}`;
            }

            // Release object URL
            URL.revokeObjectURL(audio.src);
        });


        console.log("Audio selected:", file.name);
        console.log("Type:", file.type);
        console.log("Size:", file.size, "bytes");
    });


    // ==============================
    // VOICE RECORDING
    // ==============================

    const startRecordingButton =
        document.getElementById("start-recording");

    let mediaRecorder;
    let audioChunks = [];
    let isRecording = false;


    startRecordingButton.addEventListener("click", async () => {

        // START RECORDING
        if (!isRecording) {

            try {

                const stream =
                    await navigator.mediaDevices.getUserMedia({
                        audio: true
                    });

                audioChunks = [];

                mediaRecorder = new MediaRecorder(stream);

                mediaRecorder.addEventListener("dataavailable", (event) => {

                    if (event.data.size > 0) {
                        audioChunks.push(event.data);
                    }

                });

                mediaRecorder.addEventListener("stop", () => {

                    const audioBlob = new Blob(audioChunks, {
                        type: "audio/webm"
                    });

                    const audioURL = URL.createObjectURL(audioBlob);
                    const recordedAudio = new Audio(audioURL);

                    recordedAudio.addEventListener("loadedmetadata", () => {

                        const duration = recordedAudio.duration;

                        const minutes =
                            Math.floor(duration / 60);

                        const seconds =
                            Math.floor(duration % 60);

                        const formattedDuration =
                            `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;

                        if (audioDuration) {
                            audioDuration.textContent =
                                `00:00 / ${formattedDuration}`;
                        }

                    });

                    console.log("Recording complete");

                    audioFileName.textContent =
                        "VoiceShield_Recording.webm";


                    // Create audio player
                    let audioPlayer =
                        document.getElementById("voice-audio-player");

                    if (!audioPlayer) {

                        audioPlayer =
                            document.createElement("audio");

                        audioPlayer.id =
                            "voice-audio-player";

                        audioPlayer.controls = true;

                        audioPlayer.className =
                            "voice-audio-player";

                        document
                            .querySelector(".audio-preview")
                            .appendChild(audioPlayer);
                    }

                    audioPlayer.src = audioURL;


                    // Stop microphone
                    stream
                        .getTracks()
                        .forEach(track => track.stop());

                });


                mediaRecorder.start();

                isRecording = true;

                startRecordingButton.innerHTML =
                    "<span>●</span> Stop Recording";

                console.log("Recording started");

            } catch (error) {

                console.error(
                    "Microphone access denied:",
                    error
                );

                alert(
                    "Microphone access is required to record audio."
                );
            }

        }

        // STOP RECORDING
        else {

            mediaRecorder.stop();

            isRecording = false;

            startRecordingButton.innerHTML =
                "<span>○</span> Start Recording";

            console.log("Recording stopped");
        }

    });


    // ==============================
    // VOICE ANALYSIS
    // ==============================

    const analyzeVoiceBtn =
        document.getElementById("analyze-voice");

    const resetVoiceBtn =
        document.getElementById("reset-voice");

    const threatScore =
        document.getElementById("threat-score");

    const riskBadge =
        document.getElementById("risk-badge");

    const otpStatus =
        document.getElementById("otp-status");

    const urgencyStatus =
        document.getElementById("urgency-status");

    const threatStatus =
        document.getElementById("threat-status");

    const bankStatus =
        document.getElementById("bank-status");

    const socialStatus =
        document.getElementById("social-status");

    const transcriptionMessage =
        document.getElementById("transcription-message");

    // Suspicious factor elements
    const otpFactor =
        document.getElementById("otp-factor");

    const urgencyFactor =
        document.getElementById("urgency-factor");

    const bankFactor =
        document.getElementById("bank-factor");

    const otpRiskBar =
        document.getElementById("otp-risk-bar");

    const urgencyRiskBar =
        document.getElementById("urgency-risk-bar");

    const bankRiskBar =
        document.getElementById("bank-risk-bar");



    if (analyzeVoiceBtn) {

        analyzeVoiceBtn.addEventListener("click", () => {

            // Change button to analyzing state
            analyzeVoiceBtn.disabled = true;

            analyzeVoiceBtn.textContent =
                "⏳ Analyzing Voice...";


            // Simulate analysis
            setTimeout(() => {

                // Analysis completed
                analyzeVoiceBtn.disabled = false;

                analyzeVoiceBtn.textContent =
                    "🔍 Analyze Again";




                // ==============================
                // MOCK ANALYSIS RESULTS
                // ==============================

                const results = [

                    {
                        score: 18,
                        risk: "LOW RISK"
                    },

                    {
                        score: 62,
                        risk: "MEDIUM RISK"
                    },

                    {
                        score: 96,
                        risk: "CRITICAL RISK"
                    }

                ];


                // Pick random result
                const result =
                    results[
                    Math.floor(
                        Math.random() * results.length
                    )
                    ];


                // ==============================
                // UPDATE SCORE
                // ==============================

                if (threatScore) {

                    threatScore.textContent =
                        result.score;
                }


                // ==============================
                // UPDATE RISK BADGE
                // ==============================

                if (riskBadge) {

                    riskBadge.textContent =
                        result.risk;


                    // Remove old classes
                    riskBadge.classList.remove(
                        "risk-badge--low",
                        "risk-badge--medium",
                        "risk-badge--critical"
                    );


                    // Add correct class
                    if (result.score <= 30) {

                        riskBadge.classList.add(
                            "risk-badge--low"
                        );

                    }

                    else if (result.score <= 70) {

                        riskBadge.classList.add(
                            "risk-badge--medium"
                        );

                    }

                    else {

                        riskBadge.classList.add(
                            "risk-badge--critical"
                        );
                    }
                }

                // ==============================
                // UPDATE SUSPICIOUS FACTORS
                // ==============================

                if (result.score <= 30) {

                    // LOW RISK

                    if (otpFactor)
                        otpFactor.textContent = "+5";

                    if (urgencyFactor)
                        urgencyFactor.textContent = "+3";

                    if (bankFactor)
                        bankFactor.textContent = "+2";


                    if (otpRiskBar)
                        otpRiskBar.style.width = "20%";

                    if (urgencyRiskBar)
                        urgencyRiskBar.style.width = "12%";

                    if (bankRiskBar)
                        bankRiskBar.style.width = "8%";
                }


                else if (result.score <= 70) {

                    // MEDIUM RISK

                    if (otpFactor)
                        otpFactor.textContent = "+12";

                    if (urgencyFactor)
                        urgencyFactor.textContent = "+18";

                    if (bankFactor)
                        bankFactor.textContent = "+14";


                    if (otpRiskBar)
                        otpRiskBar.style.width = "45%";

                    if (urgencyRiskBar)
                        urgencyRiskBar.style.width = "65%";

                    if (bankRiskBar)
                        bankRiskBar.style.width = "52%";
                }


                else {

                    // CRITICAL RISK

                    if (otpFactor)
                        otpFactor.textContent = "+25";

                    if (urgencyFactor)
                        urgencyFactor.textContent = "+22";

                    if (bankFactor)
                        bankFactor.textContent = "+20";


                    if (otpRiskBar)
                        otpRiskBar.style.width = "82%";

                    if (urgencyRiskBar)
                        urgencyRiskBar.style.width = "74%";

                    if (bankRiskBar)
                        bankRiskBar.style.width = "68%";
                }


                // ==============================
                // UPDATE THREAT STATUSES
                // ==============================

                if (result.score <= 30) {

                    // LOW RISK
                    if (transcriptionMessage) {
                        transcriptionMessage.innerHTML =
                            "Hello, I received a notification about my account. " +
                            "Could you please tell me what this is regarding?";
                    }
                    if (otpStatus)
                        otpStatus.textContent = "Clear";

                    if (urgencyStatus)
                        urgencyStatus.textContent = "Clear";

                    if (threatStatus)
                        threatStatus.textContent = "Clear";

                    if (bankStatus)
                        bankStatus.textContent = "Clear";

                    if (socialStatus)
                        socialStatus.textContent = "Clear";
                }


                else if (result.score <= 70) {

                    // MEDIUM RISK

                    if (transcriptionMessage) {
                        transcriptionMessage.innerHTML =
                            "Your account may have a security issue. " +
                            "<span class='transcription-highlight'>" +
                            "You need to verify your account" +
                            "</span> before we can continue.";
                    }

                    if (otpStatus)
                        otpStatus.textContent = "Clear";

                    if (urgencyStatus)
                        urgencyStatus.textContent = "Detected";

                    if (threatStatus)
                        threatStatus.textContent = "Warning";

                    if (bankStatus)
                        bankStatus.textContent = "Detected";

                    if (socialStatus)
                        socialStatus.textContent = "Warning";
                }


                else {

                    // CRITICAL RISK

                    if (transcriptionMessage) {
                        transcriptionMessage.innerHTML =
                            "Your bank account has been flagged. " +
                            "<span class='transcription-highlight'>" +
                            "You must verify your account immediately" +
                            "</span> " +
                            "or your account will be locked. Please provide the OTP.";
                    }


                    if (otpStatus)
                        otpStatus.textContent = "Detected";

                    if (urgencyStatus)
                        urgencyStatus.textContent = "Detected";

                    if (threatStatus)
                        threatStatus.textContent = "Detected";

                    if (bankStatus)
                        bankStatus.textContent = "Detected";

                    if (socialStatus)
                        socialStatus.textContent = "Detected";
                }


                console.log(
                    "Voice analysis result:",
                    result
                );

            }, 2000);
        });
    }

    // ==============================
    // RESET VOICE ANALYSIS
    // ==============================

    if (resetVoiceBtn) {

        resetVoiceBtn.addEventListener("click", () => {

            // Reset file input
            audioFileInput.value = "";

            // Reset file name
            audioFileName.textContent =
                "No audio selected";

            // Reset duration
            if (audioDuration) {
                audioDuration.textContent =
                    "00:00 / 00:00";
            }

            // Reset threat score
            if (threatScore) {
                threatScore.textContent = "—";
            }

            // Reset risk badge
            if (riskBadge) {

                riskBadge.textContent =
                    "NOT ANALYZED";

                riskBadge.classList.remove(
                    "risk-badge--low",
                    "risk-badge--medium",
                    "risk-badge--critical"
                );
            }

            // Reset threat statuses
            if (otpStatus)
                otpStatus.textContent = "—";

            if (urgencyStatus)
                urgencyStatus.textContent = "—";

            if (threatStatus)
                threatStatus.textContent = "—";

            if (bankStatus)
                bankStatus.textContent = "—";

            if (socialStatus)
                socialStatus.textContent = "—";

            // Reset suspicious factors
            if (otpFactor)
                otpFactor.textContent = "+0";

            if (urgencyFactor)
                urgencyFactor.textContent = "+0";

            if (bankFactor)
                bankFactor.textContent = "+0";

            // Reset risk bars
            if (otpRiskBar)
                otpRiskBar.style.width = "0%";

            if (urgencyRiskBar)
                urgencyRiskBar.style.width = "0%";

            if (bankRiskBar)
                bankRiskBar.style.width = "0%";

            // Reset transcription
            if (transcriptionMessage) {

                transcriptionMessage.textContent =
                    "No analysis available. Upload or record an audio file.";
            }

            // Remove recorded audio player
            const audioPlayer =
                document.getElementById("voice-audio-player");

            if (audioPlayer) {
                audioPlayer.remove();
            }

            // Reset analyze button
            if (analyzeVoiceBtn) {

                analyzeVoiceBtn.disabled = false;

                analyzeVoiceBtn.textContent =
                    "🔍 Analyze Voice";
            }

            console.log("Voice Shield reset");

        });

    }

});