% SOFC 스택 평가 시뮬레이션 결과 시각화 (MATLAB)
% 사전 준비: 프로젝트 루트에서 python -I src/run_all.py 를 먼저 실행해 out/ 을 생성
% 모든 데이터는 시뮬레이션이다.
clear; clc; close all;
root = fileparts(fileparts(mfilename('fullpath')));
out  = fullfile(root, 'out');
T = readtable(fullfile(out, 'test_data.csv'));
S = readtable(fullfile(out, 'stack_summary.csv'));
set(groot, 'defaultAxesFontName', 'Malgun Gothic');

% 1) 분극 곡선 (모델): 전류밀도 대 셀 전압과 출력밀도
i = linspace(0, 1.2, 200);
Tk = 973; F = 96485; R = 8.314;
h2 = 0.97*(1-0.7/2); h2o = 1-h2;
E  = 1.253 - 2.4516e-4*Tk + R*Tk/(2*F)*log(h2*sqrt(0.21)/h2o);
V  = E - R*Tk/(0.5*F)*asinh(i/(2*0.35)) - 0.12*i ...
       + R*Tk/(2*F)*log(max(1 - i/1.6, 1e-3));
f1 = figure('Position',[100 100 640 420]);
yyaxis left;  plot(i, V, 'LineWidth', 2); ylabel('셀 전압 [V]');
yyaxis right; plot(i, V.*i, '--', 'LineWidth', 2); ylabel('출력밀도 [W/cm^2]');
xline(0.4, ':k', '운전점 0.4 A/cm^2');
xlabel('전류밀도 [A/cm^2]'); title('분극 곡선 (모델, 시뮬레이션)'); grid on;
exportgraphics(f1, fullfile(out, 'm_polarization.png'), 'Resolution', 130);

% 2) 호기별 초기 평균 전압 박스플롯
f2 = figure('Position',[100 100 640 420]);
boxchart(categorical(S.rig), S.mean_V); hold on;
yline(0.82, 'r--', '하한(가정)');
ylabel('초기 셀 평균전압 [V]'); title('호기별 성능 분포 (시뮬레이션)'); grid on;
exportgraphics(f2, fullfile(out, 'm_rig_box.png'), 'Resolution', 130);

% 3) 열화 트렌드: 스택 평균 전압 (PASS 파랑 / FAIL 빨강)
f3 = figure('Position',[100 100 640 420]); hold on;
stacks = unique(T.stack);
for k = 1:numel(stacks)
    g = T(strcmp(T.stack, stacks{k}), :);
    [hrs, ~, idx] = unique(g.hour);
    m = accumarray(idx, g.cell_V, [], @mean);
    ok = strcmp(S.verdict(strcmp(S.stack, stacks{k})), 'PASS');
    if ok, c = [0.2 0.4 0.8 0.35]; else, c = [0.85 0.2 0.2 0.5]; end
    plot(hrs, m, 'Color', c);
end
xlabel('시간 [h]'); ylabel('스택 평균 셀전압 [V]');
title('트렌드: 파랑 PASS / 빨강 FAIL (시뮬레이션)'); grid on;
exportgraphics(f3, fullfile(out, 'm_trend.png'), 'Resolution', 130);

% 4) 결함 스택 한 개의 셀별 전압 히트맵 (가스 누설로 분류된 첫 스택)
idxLeak = find(strcmp(S.cause, 'gas_leak'), 1);
if ~isempty(idxLeak)
    sid = S.stack{idxLeak};
    g = T(strcmp(T.stack, sid), :);
    hrs = unique(g.hour); cells = unique(g.cell);
    M = zeros(numel(cells), numel(hrs));
    for a = 1:numel(cells)
        for b = 1:numel(hrs)
            M(a,b) = g.cell_V(g.cell==cells(a) & g.hour==hrs(b));
        end
    end
    f4 = figure('Position',[100 100 640 420]);
    imagesc(hrs, cells, M); colorbar; axis xy;
    xlabel('시간 [h]'); ylabel('셀 번호');
    title(sprintf('%s 셀별 전압 (시뮬레이션)', sid));
    exportgraphics(f4, fullfile(out, 'm_cell_heatmap.png'), 'Resolution', 130);
end

% 5) 열화율 대 최저 셀 전압: 판정 경계 확인
f5 = figure('Position',[100 100 640 420]); hold on;
ok = strcmp(S.verdict, 'PASS');
scatter(S.deg_pct_kh(ok),  S.min_cell_V(ok),  40, 'b', 'filled');
scatter(S.deg_pct_kh(~ok), S.min_cell_V(~ok), 40, 'r', 'filled');
yline(0.78, 'k--', '셀 전압 하한(가정)');
xlabel('열화율 [%/1000h]'); ylabel('초기 최저 셀 전압 [V]');
legend('PASS', 'FAIL', 'Location', 'best'); grid on;
title('판정 경계 (시뮬레이션)');
exportgraphics(f5, fullfile(out, 'm_decision.png'), 'Resolution', 130);
disp('MATLAB 그래프 5장을 out/ 에 저장했습니다.');
