async function checkStatus(){

    const response = await fetch(
        `/report/status?address=${address}`
    );

    const status = await response.json();

    if(status.complete){

        document.getElementById("loadingState").style.display="none";

        document.getElementById("completeState").style.display="block";

        document.getElementById("reportContent").style.display="block";

        loadReport();

    }
    else{

        setTimeout(checkStatus,2000);

    }

}

checkStatus();