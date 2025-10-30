readChannelID = 2259272;
KeyID = 4;
readAPIKey = '6K8USYMEOC2V3SXS';

% Try to read data from the last 360 minutes
try
    [data, timeStamps] = thingSpeakRead(readChannelID, 'Fields', [KeyID], ...
                                                       'NumMinutes', 360, ...
                                                       'ReadKey', readAPIKey);
catch
    data = [];
    timeStamps = [];
end

% If no data in last 360 minutes, get the most recent available data
if isempty(data) || isempty(timeStamps)
    warning('No data in last 360 minutes. Fetching last 100 available data points.');
    try
        [data, timeStamps] = thingSpeakRead(readChannelID, 'Fields', [KeyID], ...
                                                           'NumPoints', 100, ...
                                                           'ReadKey', readAPIKey);
    catch ME
        error('Unable to retrieve any data from ThingSpeak: %s', ME.message);
    end
end

% Check if we have data to plot
if isempty(data) || isempty(timeStamps)
    error('No data available from channel %d', readChannelID);
end

keyData = data(:,1);

h2a = scatter(timeStamps, keyData, 350, '|');
ylabel('Key Pressed');
yticks([0 1 2 3 4 5 6 7 8 9]);
ylim([0 9]);
grid on;

tickvals = xticks;
xax = get(gca, 'XAxis');
xtickangle(-65);

set(gca, 'XMinorTick', 'on')
a = tickvals(1);
b = diff(tickvals(1:2))/6;
c = tickvals(end);
xax.MinorTickValues = a:b:c;

grid minor

xax.FontSize = 7;
datetick('x', 16);
xlim padded;
