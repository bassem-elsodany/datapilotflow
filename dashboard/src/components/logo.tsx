import { Box, BoxProps, ElementProps } from '@mantine/core';
import appLogo from '@/assets/app-logo.svg';

interface LogoProps
  extends Omit<BoxProps, 'children' | 'ref'>,
    ElementProps<'img', keyof BoxProps> {
  size?: string | number;
  height?: string | number;
}

export function Logo({ size, height, style, ...props }: LogoProps) {
  // DataPilotFlow logo aspect ratio: 75.78:33.981 ≈ 2.23:1
  const aspectRatio = 75.78 / 33.981;
  
  let finalWidth = size;
  let finalHeight = height;
  
  if (size && !height) {
    // If only size is provided, calculate height to maintain aspect ratio
    finalHeight = typeof size === 'number' ? size / aspectRatio : `calc(${size} / ${aspectRatio})`;
  } else if (height && !size) {
    // If only height is provided, calculate width to maintain aspect ratio
    finalWidth = typeof height === 'number' ? height * aspectRatio : `calc(${height} * ${aspectRatio})`;
  } else if (!size && !height) {
    // Default dimensions if neither size nor height is provided
    finalWidth = '120px';
    finalHeight = '54px';
  }

  return (
    <Box
      component="img"
      src={appLogo}
      alt="DataPilotFlow Logo"
      width={finalWidth}
      height={finalHeight}
      style={{
        display: 'block',
        maxWidth: '100%',
        height: 'auto',
        imageRendering: 'auto',
        ...style,
      }}
      {...props}
    />
  );
}
