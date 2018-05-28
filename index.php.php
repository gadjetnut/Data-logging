<?php
    include ("dblogger.php");
    echo "The last 10 temperature logs are:";
    echo DisplayTelemetryLog(10);
?>