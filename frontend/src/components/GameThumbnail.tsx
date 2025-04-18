import React, { memo } from 'react';

type Props = {
  thumbUrl: string;
};

const GameThumbnailComponent: React.FC<Props> = ({ thumbUrl }) => {
  return (
    <img
      src={thumbUrl}
      style={{
        width: '100%',
        height: 200,
        border: 'none',
        pointerEvents: 'none',
        marginTop: 8,
        backgroundColor: '#fff',
        overflow: 'hidden',
      }}
    />
  )
};

export const GameThumbnail = memo(GameThumbnailComponent)
