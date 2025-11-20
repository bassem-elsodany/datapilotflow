import { Box, Card, Group, Stack, Text, Transition, useMantineTheme } from '@mantine/core';
import { IconCheck } from '@tabler/icons-react';
import { ReactNode } from 'react';
import styles from './colorful-vertical-stepper.module.css';

export interface StepConfig {
  label: string;
  description: string;
  icon: ReactNode;
  color: string;
  gradientFrom?: string;
  gradientTo?: string;
}

interface ColorfulVerticalStepperProps {
  activeStep: number;
  completedSteps: number[];
  steps: StepConfig[];
  children: ReactNode;
  onStepClick?: (step: number) => void;
  isEditMode?: boolean;
}

export function ColorfulVerticalStepper({
  activeStep,
  completedSteps,
  steps,
  children,
  onStepClick,
  isEditMode = false
}: ColorfulVerticalStepperProps) {
  const theme = useMantineTheme();

  const isStepCompleted = (step: number) => completedSteps.includes(step);
  const isStepActive = (step: number) => step === activeStep;
  const isStepClickable = (step: number) => {
    // In edit mode, all steps are clickable
    if (isEditMode) {
      return true;
    }
    // In create mode, allow clicking:
    // - Previous steps (go back)
    // - Completed steps (revisit)
    // - Immediate next step (advance forward)
    return step < activeStep || completedSteps.includes(step) || step === activeStep + 1;
  };

  return (
    <Group align="flex-start" gap="lg" wrap="nowrap" style={{ minHeight: '520px' }}>
      {/* Vertical Progress Tracker */}
      <Box style={{ width: '200px', flexShrink: 0 }}>
        <Stack gap="xs">
          {steps.map((step, index) => {
            const completed = isStepCompleted(index);
            const active = isStepActive(index);
            const clickable = isStepClickable(index);

            return (
              <Box key={index} style={{ position: 'relative' }}>
                {/* Connecting Line */}
                {index < steps.length - 1 && (
                  <Box
                    className={styles.connectingLine}
                    style={{
                      position: 'absolute',
                      left: '20px',
                      top: '42px',
                      width: '2px',
                      height: '28px',
                      background: completed
                        ? `linear-gradient(180deg, ${step.color} 0%, ${steps[index + 1].color} 100%)`
                        : '#e9ecef',
                      transition: 'all 0.4s ease',
                      zIndex: 0
                    }}
                  />
                )}

                {/* Circular Step Design */}
                <Box
                  className={`${styles.stepCard} ${active ? styles.active : ''} ${completed ? styles.completed : ''}`}
                  style={{
                    cursor: clickable ? 'pointer' : 'default',
                    position: 'relative',
                    zIndex: active ? 2 : 1,
                    opacity: clickable || active ? 1 : 0.7,
                    transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)'
                  }}
                  onClick={() => clickable && onStepClick?.(index)}
                >
                  <Group gap="sm" wrap="nowrap" align="center">
                    {/* Compact Circular Icon */}
                    <Box style={{ position: 'relative' }}>
                      <Box
                        className={active ? styles.pulseAnimation : ''}
                        style={{
                          width: '38px',
                          height: '38px',
                          borderRadius: '50%',
                          background: completed
                            ? `linear-gradient(135deg, ${step.color} 0%, ${step.gradientTo || step.color} 100%)`
                            : active
                              ? `linear-gradient(135deg, ${step.color}15 0%, ${step.gradientTo || step.color}25 100%)`
                              : `linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%)`,
                          border: completed
                            ? `2px solid ${step.color}`
                            : active
                              ? `2px solid ${step.color}`
                              : '2px solid #dee2e6',
                          boxShadow: active
                            ? `0 4px 12px ${step.color}25, 0 0 0 3px ${step.color}08`
                            : completed
                              ? `0 2px 8px ${step.color}15`
                              : '0 1px 3px rgba(0,0,0,0.05)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          color: completed ? 'white' : active ? step.color : theme.colors.gray[5],
                          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                          transform: active ? 'scale(1.08)' : 'scale(1)',
                          position: 'relative',
                          overflow: 'visible'
                        }}
                      >
                        <Box style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                          {step.icon}
                        </Box>

                        {/* Subtle rotating ring for active only */}
                        {active && (
                          <Box
                            className={styles.rotatingRing}
                            style={{
                              position: 'absolute',
                              width: '46px',
                              height: '46px',
                              borderRadius: '50%',
                              border: `2px solid transparent`,
                              borderTopColor: step.color,
                              borderRightColor: step.color,
                              opacity: 0.3,
                              animation: 'rotate 3s linear infinite'
                            }}
                          />
                        )}

                        {/* Step Number Badge (smaller) */}
                        {!completed && (
                          <Box
                            style={{
                              position: 'absolute',
                              top: -4,
                              right: -4,
                              width: '16px',
                              height: '16px',
                              borderRadius: '50%',
                              background: active
                                ? `linear-gradient(135deg, ${step.color} 0%, ${step.gradientTo || step.color} 100%)`
                                : '#868e96',
                              color: 'white',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              fontSize: '9px',
                              fontWeight: 700,
                              border: '2px solid white',
                              boxShadow: active
                                ? `0 2px 6px ${step.color}30`
                                : '0 1px 3px rgba(0,0,0,0.1)',
                              transition: 'all 0.3s ease'
                            }}
                          >
                            {index + 1}
                          </Box>
                        )}
                      </Box>
                    </Box>

                    {/* Step Info */}
                    <Stack gap={4} style={{ flex: 1 }}>
                      <Text
                        size="sm"
                        fw={active ? 700 : completed ? 600 : 500}
                        style={{
                          color: active ? step.color : completed ? theme.colors.dark[7] : theme.colors.gray[6],
                          transition: 'all 0.3s ease',
                          letterSpacing: active ? '0.3px' : '0px'
                        }}
                      >
                        {step.label}
                      </Text>
                      <Text
                        size="xs"
                        c="dimmed"
                        style={{
                          lineHeight: 1.4,
                          opacity: active ? 1 : 0.75
                        }}
                      >
                        {step.description}
                      </Text>

                      {/* Progress indicator for active */}
                      {active && (
                        <Box
                          style={{
                            width: '100%',
                            height: '2px',
                            borderRadius: '2px',
                            background: `linear-gradient(90deg, ${step.color} 0%, ${step.gradientTo || step.color} 100%)`,
                            marginTop: '2px',
                            opacity: 0.6
                          }}
                        />
                      )}
                    </Stack>
                  </Group>
                </Box>
              </Box>
            );
          })}
        </Stack>
      </Box>

      {/* Content Area */}
      <Box style={{ flex: 1, minWidth: 0 }}>
        <Transition
          mounted={true}
          transition="fade"
          duration={300}
          timingFunction="ease"
        >
          {(transitionStyles) => (
            <Card
              className={styles.contentCard}
              padding="lg"
              radius="lg"
              withBorder
              shadow="sm"
              style={{
                ...transitionStyles,
                border: `1px solid ${steps[activeStep]?.color}20`,
                boxShadow: `0 4px 20px ${steps[activeStep]?.color}10, 0 1px 3px rgba(0,0,0,0.05)`,
                background: 'linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%)',
                minHeight: '440px',
                position: 'relative',
                overflow: 'visible'
              }}
            >
              {/* Decorative gradient accent */}
              <Box
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  right: 0,
                  height: '4px',
                  background: `linear-gradient(90deg, ${steps[activeStep]?.color} 0%, ${steps[activeStep]?.gradientTo || steps[activeStep]?.color} 100%)`,
                  borderRadius: '12px 12px 0 0'
                }}
              />

              {/* Content */}
              <Box style={{ paddingTop: '6px' }}>
                {children}
              </Box>
            </Card>
          )}
        </Transition>
      </Box>
    </Group>
  );
}
