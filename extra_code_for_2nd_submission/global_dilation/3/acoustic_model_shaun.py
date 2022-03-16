import tensorflow as tf
from self_defined import get_name_scope


def bn_relu_fn(inputs):
    assert get_name_scope() != ''

    outputs = inputs

    outputs = tf.keras.layers.BatchNormalization(
        name=get_name_scope() + 'bn',
        scale=False
    )(outputs)

    outputs = tf.keras.layers.ReLU(
        name=get_name_scope() + 'relu'
    )(outputs)

    return outputs


def create_acoustic_model_fn(global_dilation):

    assert global_dilation in range(1, 5)

    inputs = tf.keras.Input([None, 540], batch_size=1, name='cqt-shaun')
    outputs = inputs
    outputs = outputs[..., None]

    with tf.name_scope('local'):
        for layer_idx in range(4):
            with tf.name_scope('layer_{}'.format(layer_idx)):

                outputs = tf.keras.layers.Conv2D(
                    name=get_name_scope() + 'conv',
                    kernel_size=[1, 5] if layer_idx == 0 else [3, 5],
                    dilation_rate=[2 ** layer_idx, 1],
                    padding='SAME',
                    use_bias=False,
                    activation=None,
                    filters=16
                )(outputs)
                outputs.set_shape([None, None, 540, None])

                outputs = bn_relu_fn(outputs)

                if layer_idx > 0:
                    outputs = tf.keras.layers.Dropout(
                        name=get_name_scope() + 'dropout',
                        rate=.2
                    )(outputs)

    with tf.name_scope('global'):

        k = 4 * 60 // global_dilation
        assert k * global_dilation == 4 * 60
        k = 1 + 2 * k

        outputs = tf.pad(outputs, [[0, 0], [0, 0], [240, 60], [0, 0]])
        outputs = tf.keras.layers.Conv2D(
            name=get_name_scope() + 'conv',
            kernel_size=[1, k],
            dilation_rate=[1, global_dilation],
            padding='VALID',
            use_bias=False,
            activation=None,
            filters=128,
            kernel_regularizer=tf.keras.regularizers.l2(1e-4)
        )(outputs)
        outputs.set_shape([None, None, 360, 128])
        outputs = bn_relu_fn(outputs)
        outputs = tf.keras.layers.Dropout(
            name=get_name_scope() + 'dropout',
            rate=.2
        )(outputs)

    with tf.name_scope('output'):

        with tf.name_scope('fusion'):
            outputs = tf.keras.layers.Dense(
                name=get_name_scope() + 'dense',
                use_bias=False,
                units=64,
                activation=None
            )(outputs)
            outputs = bn_relu_fn(outputs)
            outputs = tf.keras.layers.Dropout(
                name=get_name_scope() + 'dropout',
                rate=.2
            )(outputs)

        with tf.name_scope('output'):
            outputs = tf.keras.layers.Dense(
                name=get_name_scope() + 'dense',
                use_bias=True,
                units=1,
                activation=None
            )(outputs)
            outputs.set_shape([1, None, 360, 1])
            outputs = tf.squeeze(outputs, axis=[0, -1])

    model = tf.keras.Model(inputs, outputs, name='shaun acoustic model')

    return model


if __name__ == '__main__':

    model = create_acoustic_model_fn(global_dilation=2)
    model.summary(line_length=150)

    for idx, w in enumerate(model.trainable_variables):
        print(idx, w.name, w.shape, w.device)

    inputs = tf.random.normal([1, 1200, 540])
    outputs = model(inputs)
    print(outputs.shape)










