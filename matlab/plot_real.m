% 공개 실측 분극 곡선(Zenodo 5763484), 열화 탐지 결과, 판정 기준표를 MATLAB으로 시각화
% 사전 준비: python -I src/analyze_real.py, degradation.py, decision_table.py 실행으로 out/ 생성
% 열화 데이터는 시뮬레이션이다.
clear; clc; close all;
root = fileparts(fileparts(mfilename('fullpath')));
out  = fullfile(root, 'out');
set(groot, 'defaultAxesFontName', 'Malgun Gothic');

IV = readtable(fullfile(out, 'real_iv_curves.csv'));
P  = readtable(fullfile(out, 'real_fit_params.csv'));
temps = [700 750 800]; col = lines(3);

% 1) 온도별 실측 분극 곡선 + 선형 구간 외삽, 선형 구간 시작 표시
f1 = figure('Position',[100 100 700 450]); hold on;
for k = 1:3
    g = IV(IV.T_C == temps(k), :);
    plot(g.j_A_cm2, g.V, 'o', 'Color', col(k,:), 'MarkerFaceColor', col(k,:), 'DisplayName', sprintf('%d °C', temps(k)));
    r = P(P.T_C == temps(k), :);
    jj = [0 max(g.j_A_cm2)];
    plot(jj, r.V0_intercept - r.R_lin*jj, '--', 'Color', col(k,:), 'HandleVisibility', 'off');
end
xline(0.3, ':k', '선형 구간 시작');
xlabel('전류밀도 [A/cm^2]'); ylabel('셀 전압 [V]'); grid on; legend('Location','northeast');
title('온도별 분극 곡선 (실측, Zenodo 5763484)');
exportgraphics(f1, fullfile(out, 'm_real_polarization.png'), 'Resolution', 130);

% 2) 750 °C 손실 구간 분해 (활성화 등 / 옴+선형 분극저항)
f2 = figure('Position',[100 100 700 450]);
g = IV(IV.T_C == 750 & IV.j_A_cm2 > 0, :);
r = P(P.T_C == 750, :);
total = (r.OCV - g.V) * 1000;
ohm   = r.R_lin * g.j_A_cm2 * 1000;
area([g.j_A_cm2], [total - ohm, ohm]);
legend({'활성화 등 (총손실 - 옴)', '옴 + 선형 분극저항'}, 'Location', 'northwest');
xlabel('전류밀도 [A/cm^2]'); ylabel('전압 손실 [mV]'); grid on;
title('750 °C 손실 구간 분해 (실측 기반)');
exportgraphics(f2, fullfile(out, 'm_real_loss_split.png'), 'Resolution', 130);

% 3) 시뮬레이션 장기 운전 전압과 탐지된 이벤트
L  = readtable(fullfile(out, 'sim_long_run.csv'));
EV = readtable(fullfile(out, 'degradation_events.csv'));
f3 = figure('Position',[100 100 760 450]);
plot(L.hour, L.V, 'Color', [0.5 0.5 0.5]); hold on;
b = L.hour <= 500; c = polyfit(L.hour(b), L.V(b), 1);
plot(L.hour, polyval(c, L.hour), 'g--', 'LineWidth', 1.5);
for k = 1:height(EV)
    if strcmp(EV.type{k}, 'step_drop'), clr = 'r'; else, clr = [1 0.6 0]; end
    xline(EV.hour(k), ':', EV.type{k}, 'Color', clr, 'Interpreter', 'none');
end
xlabel('시간 [h]'); ylabel('전압 [V]'); grid on;
legend({'전압', '초기 기준 외삽'}, 'Location', 'southwest');
title('장기 운전 전압과 탐지된 이벤트 (시뮬레이션)');
exportgraphics(f3, fullfile(out, 'm_sim_degradation.png'), 'Resolution', 130);

% 4) 판정 기준표 (표 그림)
D = readtable(fullfile(out, 'decision_table.csv'), 'VariableNamingRule', 'preserve');
f4 = uifigure('Position', [100 100 1500 330], 'Name', '시운전 합·부 판정 기준표');
t = uitable(f4, 'Data', D, 'Position', [10 10 1480 310], 'FontSize', 12, ...
    'ColumnWidth', {70, 190, 260, 170, 270, 440}, 'RowName', {});
drawnow;
try
    exportapp(f4, fullfile(out, 'm_decision_table.png'));
catch ME
    disp(['표 그림 저장 실패: ' ME.message]);
end
disp('MATLAB 그래프를 out/ 에 저장했습니다.');
