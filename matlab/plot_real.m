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
legend({'비선형 성분 (총손실 - 선형 저항분)', '선형 구간 저항분 (옴+분극+연료이용 영향)'}, 'Location', 'northwest');
xlabel('전류밀도 [A/cm^2]'); ylabel('전압 손실 [mV]'); grid on;
title('750 °C 손실 구간 분리 (실측 기반, 곡선 형상 기준)');
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

% 4) 판정 기준표 (일반 그림에 직접 그려 긴 문구를 줄바꿈한다)
D = readtable(fullfile(out, 'decision_table.csv'), 'VariableNamingRule', 'preserve');
hdr = D.Properties.VariableNames;
wid = [0.06 0.17 0.19 0.12 0.17 0.29];            % 열 너비(비율)
nch = [5 14 30 12 18 30];                           % 열별 줄바꿈 글자 수(한글 기준 근사)
f4 = figure('Position', [100 100 1600 520], 'Color', 'w');
ax = axes(f4, 'Position', [0.01 0.02 0.98 0.96]); axis(ax, 'off'); xlim(ax, [0 1]); ylim(ax, [0 1]);
x0 = [0 cumsum(wid(1:end-1))]; nrow = height(D);
rh = 1 / (nrow + 1.2);
for c = 1:numel(hdr)
    text(ax, x0(c) + 0.005, 1 - rh*0.5, hdr{c}, 'FontWeight', 'bold', 'FontSize', 11, 'VerticalAlignment', 'middle');
end
line(ax, [0 1], [1 - rh, 1 - rh], 'Color', 'k');
for r = 1:nrow
    yc = 1 - rh*(r + 0.1) - rh*0.5;
    if mod(r, 2) == 0, patch(ax, [0 1 1 0], yc + rh*0.5*[-1 -1 1 1] , [0.95 0.95 0.95], 'EdgeColor', 'none'); end
    for c = 1:numel(hdr)
        t = string(D{r, c});
        t = strjoin(arrayfun(@(k) extractBetween(t, k, min(k + nch(c) - 1, strlength(t))), 1:nch(c):strlength(t)), newline);
        text(ax, x0(c) + 0.005, yc, t, 'FontSize', 9.5, 'VerticalAlignment', 'middle', 'Interpreter', 'none');
    end
end
exportgraphics(f4, fullfile(out, 'm_decision_table.png'), 'Resolution', 130);
disp('MATLAB 그래프를 out/ 에 저장했습니다.');
