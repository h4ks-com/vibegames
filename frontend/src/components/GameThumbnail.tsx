import React, { memo } from 'react';

type Props = {
  baseUrl: string;
  name: string;
};

const GameThumbnailComponent: React.FC<Props> = ({ baseUrl, name }) => {
  const randomSeed = Math.floor(Math.random() * 1000);
  const url = `${baseUrl}?seed=${randomSeed}&count=false`;
  return (
    <iframe
      src={url}
      title={`${name} preview`}
      style={{
        width: '100%',
        height: 200,
        border: 'none',
        pointerEvents: 'none',
        marginTop: 8,
        backgroundColor: '#fff',
        overflow: 'hidden',
      }}
      seamless
      scrolling="no"
    />
  )
};

export const GameThumbnail = memo(GameThumbnailComponent)
