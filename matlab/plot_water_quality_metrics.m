function plot_water_quality_metrics(outputDir)
%PLOT_WATER_QUALITY_METRICS Plot synthetic water-quality lab outputs.
% Usage: plot_water_quality_metrics('outputs')

if nargin < 1
    outputDir = 'outputs';
end
riskPath = fullfile(outputDir, 'results', 'synthetic_treatment_risk.csv');
alertPath = fullfile(outputDir, 'results', 'synthetic_alert_signals.csv');

if isfile(riskPath)
    risk = readtable(riskPath);
    figure;
    bar(categorical(risk.station_id), risk.treatment_risk_score);
    title('Synthetic Treatment Risk by Station');
    xlabel('Station');
    ylabel('Risk score');
    xtickangle(45);
end

if isfile(alertPath)
    alerts = readtable(alertPath);
    figure;
    histogram(categorical(alerts.alert_priority));
    title('Synthetic Alert Priority Distribution');
    xlabel('Priority');
    ylabel('Station count');
end
end
